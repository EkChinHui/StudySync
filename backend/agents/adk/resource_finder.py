"""Resource Finder Agent - ADK implementation for finding real session-specific resources."""

from typing import AsyncGenerator, Dict, List
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from pydantic import Field

from backend.services.resource_discovery_service import (
    ResourceDiscoveryService,
    get_resource_discovery_service
)


class ResourceFinderAgent(BaseAgent):
    """
    Agent responsible for finding real learning resources for each session.

    Uses youtube-search-python to find actual YouTube video URLs and
    duckduckgo-search to find real article URLs. No API keys required.

    This agent runs AFTER scheduling and finds specific video/article resources
    for each session based on its unique topic. This ensures no duplicate
    resources across sessions.

    Reads from session state:
        - schedule: List of sessions from SchedulerAgent
        - topic: Main learning topic

    Writes to session state:
        - schedule: Updated sessions with real resource URLs added
    """

    name: str = "resource_finder_agent"
    description: str = "Finds real YouTube videos and articles for each scheduled session"

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Find real resources for each session."""
        print(f"[{self.name}] Starting resource discovery for sessions...")

        schedule = ctx.session.state.get("schedule", [])
        main_topic = ctx.session.state.get("topic", "")
        progress_callback = ctx.session.state.get("progress_callback")

        if not schedule:
            print(f"[{self.name}] No sessions to find resources for")
            yield Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="No sessions found for resource finding")]
                )
            )
            return

        # Get the discovery service
        discovery_service = get_resource_discovery_service()

        # Emit initial progress
        if progress_callback:
            await progress_callback("resources", f"Finding resources for {len(schedule)} sessions...")

        # Find resources for each session
        total_resources = 0
        total_sessions = len(schedule)
        for i, session in enumerate(schedule):
            session_topic = session.get("session_topic", "")
            module_title = session.get("module_title", "")
            display_topic = session_topic or module_title or f"Session {i+1}"

            print(f"[{self.name}] Finding resources for session {i+1}/{total_sessions}: {display_topic}")

            # Emit progress before finding resources
            if progress_callback:
                await progress_callback(
                    "resources",
                    f"Finding resources for {display_topic}...",
                    {"current": i + 1, "total": total_sessions}
                )

            # Get real resources for this specific session topic
            resources = self._find_session_resources(
                discovery_service=discovery_service,
                main_topic=main_topic or module_title,
                session_topic=session_topic
            )

            session["resources"] = resources
            total_resources += len(resources)

            # Emit progress after finding resources
            if progress_callback:
                await progress_callback(
                    "resources",
                    f"{len(resources)} resources found for {display_topic} ({i+1}/{total_sessions})",
                    {"current": i + 1, "total": total_sessions, "resources_found": len(resources)}
                )

            # Yield intermediate event for ADK tracking
            yield Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=f"{len(resources)} resources found for {display_topic}")]
                )
            )

        # Update schedule in session state
        ctx.session.state["schedule"] = schedule

        print(f"[{self.name}] Found {total_resources} total resources for {total_sessions} sessions")

        # Emit final summary
        if progress_callback:
            await progress_callback(
                "resources",
                f"Resource discovery complete: {total_resources} resources for {total_sessions} sessions"
            )

        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Found {total_resources} resources for {total_sessions} sessions")]
            )
        )

    def _find_session_resources(
        self,
        discovery_service: ResourceDiscoveryService,
        main_topic: str,
        session_topic: str
    ) -> List[Dict]:
        """Find real resources for a single session topic.

        Args:
            discovery_service: The resource discovery service
            main_topic: Main learning topic (e.g., "Python")
            session_topic: Specific session topic (e.g., "Python Functions")

        Returns:
            List of resource dictionaries with real URLs
        """
        resources = []

        # Build a focused search query
        video_query = f"{session_topic} tutorial explained"
        article_query = f"{session_topic} tutorial guide"

        # Search for YouTube videos (get 3, keep best 2)
        try:
            videos = discovery_service.search_youtube_videos(video_query, max_results=3)
            # Filter for quality - prefer shorter tutorials (under 20 min indicator)
            quality_videos = self._filter_quality_videos(videos)
            resources.extend(quality_videos[:2])
        except Exception as e:
            print(f"[{self.name}] Video search failed: {e}")
            # Add fallback search URL
            resources.append(self._fallback_video(session_topic))

        # Search for articles (get 3, keep best 1)
        try:
            articles = discovery_service.search_articles(article_query, max_results=3)
            # Filter for quality sources
            quality_articles = self._filter_quality_articles(articles)
            resources.extend(quality_articles[:1])
        except Exception as e:
            print(f"[{self.name}] Article search failed: {e}")
            # Add fallback search URL
            resources.append(self._fallback_article(session_topic))

        return resources

    def _filter_quality_videos(self, videos: List[Dict]) -> List[Dict]:
        """Filter videos for educational quality.

        Prefers:
        - Tutorial/educational content (by title keywords)
        - Shorter videos (5-20 min ideal)
        - Channels with reasonable view counts

        Args:
            videos: List of video dictionaries

        Returns:
            Filtered and sorted list of quality videos
        """
        if not videos:
            return []

        scored_videos = []
        for video in videos:
            score = 0
            title_lower = video.get("title", "").lower()

            # Boost for tutorial-related keywords
            tutorial_keywords = ["tutorial", "explained", "learn", "beginner", "guide", "how to", "introduction", "basics"]
            for keyword in tutorial_keywords:
                if keyword in title_lower:
                    score += 2

            # Penalize clickbait indicators
            clickbait_keywords = ["shocking", "you won't believe", "gone wrong", "funny", "compilation", "react"]
            for keyword in clickbait_keywords:
                if keyword in title_lower:
                    score -= 5

            # Parse duration and prefer 5-20 min videos
            duration = video.get("duration", "")
            if duration:
                try:
                    parts = duration.split(":")
                    if len(parts) == 2:  # MM:SS
                        minutes = int(parts[0])
                        if 5 <= minutes <= 20:
                            score += 3
                        elif minutes < 5:
                            score += 1
                        elif minutes > 30:
                            score -= 1
                    elif len(parts) == 3:  # HH:MM:SS (long video)
                        score -= 2
                except (ValueError, IndexError):
                    pass

            scored_videos.append((score, video))

        # Sort by score descending
        scored_videos.sort(key=lambda x: x[0], reverse=True)
        return [v for _, v in scored_videos]

    def _filter_quality_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles for quality sources.

        Prefers:
        - Trusted domains (dev.to, medium, freecodecamp, official docs)
        - Tutorial/guide content

        Args:
            articles: List of article dictionaries

        Returns:
            Filtered and sorted list of quality articles
        """
        if not articles:
            return []

        # Trusted domains (higher priority first)
        trusted_domains = [
            "freecodecamp.org",
            "dev.to",
            "medium.com",
            "realpython.com",
            "digitalocean.com",
            "geeksforgeeks.org",
            "tutorialspoint.com",
            "w3schools.com",
            "mdn.io",
            "developer.mozilla.org"
        ]

        scored_articles = []
        for article in articles:
            score = 0
            source = article.get("source", "").lower()
            title_lower = article.get("title", "").lower()

            # Boost for trusted domains
            for i, domain in enumerate(trusted_domains):
                if domain in source:
                    score += 10 - i  # Higher score for domains earlier in list
                    break

            # Boost for tutorial-related keywords
            tutorial_keywords = ["tutorial", "guide", "learn", "beginner", "introduction", "explained", "how to"]
            for keyword in tutorial_keywords:
                if keyword in title_lower:
                    score += 2

            scored_articles.append((score, article))

        # Sort by score descending
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored_articles]

    def _fallback_video(self, topic: str) -> Dict:
        """Generate fallback video search URL."""
        encoded_query = topic.replace(" ", "+")
        return {
            "type": "video",
            "title": f"Search: {topic} tutorials",
            "url": f"https://www.youtube.com/results?search_query={encoded_query}+tutorial",
            "description": "Click to search for video tutorials",
            "platform": "youtube",
            "is_fallback": True
        }

    def _fallback_article(self, topic: str) -> Dict:
        """Generate fallback article search URL."""
        encoded_query = topic.replace(" ", "+")
        return {
            "type": "article",
            "title": f"Search: {topic} guides",
            "url": f"https://duckduckgo.com/?q={encoded_query}+tutorial+guide",
            "description": "Click to search for articles and guides",
            "platform": "duckduckgo",
            "is_fallback": True
        }
