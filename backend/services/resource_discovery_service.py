"""Resource Discovery Service for finding real YouTube videos and articles.

Uses pytubefix and ddgs to find actual URLs without requiring API keys.
"""

from typing import Dict, List, Optional
from urllib.parse import quote_plus

# Singleton instance
_service_instance = None


class ResourceDiscoveryService:
    """Service for discovering educational resources from YouTube and the web."""

    def __init__(self):
        """Initialize the resource discovery service."""
        self._pytubefix_search = None
        self._ddg_search = None
        self._llm_service = None

    def _get_llm_service(self):
        """Lazy load LLM service for relevance checking."""
        if self._llm_service is None:
            try:
                from backend.services.llm_service import LLMService
                self._llm_service = LLMService()
            except Exception as e:
                print(f"[ResourceDiscoveryService] Could not load LLM service: {e}")
                self._llm_service = False
        return self._llm_service

    def _get_youtube_search(self):
        """Lazy load YouTube search from pytubefix."""
        if self._pytubefix_search is None:
            try:
                from pytubefix import Search
                self._pytubefix_search = Search
            except ImportError:
                print("[ResourceDiscoveryService] pytubefix not installed")
                self._pytubefix_search = False
        return self._pytubefix_search

    def _get_ddg_search(self):
        """Lazy load DuckDuckGo search."""
        if self._ddg_search is None:
            try:
                from ddgs import DDGS
                self._ddg_search = DDGS
            except ImportError:
                print("[ResourceDiscoveryService] ddgs not installed")
                self._ddg_search = False
        return self._ddg_search

    def search_youtube_videos(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search YouTube for videos matching the query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of video dictionaries with keys:
            - type: "video"
            - title: Video title
            - url: Direct YouTube watch URL
            - duration: Video duration string
            - channel: Channel name
            - views: View count string
            - thumbnail: Thumbnail URL
            - platform: "youtube"
        """
        Search = self._get_youtube_search()

        if not Search:
            return self._fallback_youtube_results(query, max_results)

        try:
            search = Search(query)
            # Get video results (not shorts)
            results = search.videos[:max_results]

            videos = []
            for yt in results:
                video = {
                    "type": "video",
                    "title": yt.title or "",
                    "url": yt.watch_url or "",
                    "duration": str(yt.length) if yt.length else "",
                    "channel": yt.author or "",
                    "views": str(yt.views) if yt.views else "",
                    "thumbnail": yt.thumbnail_url or "",
                    "platform": "youtube"
                }
                videos.append(video)

            print(f"[ResourceDiscoveryService] Found {len(videos)} YouTube videos for: {query}")
            return videos

        except Exception as e:
            print(f"[ResourceDiscoveryService] YouTube search error: {e}")
            return self._fallback_youtube_results(query, max_results)

    def search_articles(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for articles using DuckDuckGo.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of article dictionaries with keys:
            - type: "article"
            - title: Article title
            - url: Direct article URL
            - description: Article snippet/description
            - source: Domain name
            - platform: "web"
        """
        DDGS = self._get_ddg_search()

        if not DDGS:
            return self._fallback_article_results(query, max_results)

        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=max_results))

            articles = []
            # Domains to exclude (not useful for learning guides, or already covered by video search)
            excluded_domains = ["wikipedia.org", "en.wikipedia.org", "simple.wikipedia.org", "youtube.com", "youtu.be"]

            for item in results:
                url = item.get("href", "")
                # Extract domain for source
                source = ""
                if url:
                    try:
                        from urllib.parse import urlparse
                        source = urlparse(url).netloc.replace("www.", "")
                    except Exception:
                        pass

                # Skip excluded domains
                if any(excluded in source for excluded in excluded_domains):
                    continue

                article = {
                    "type": "article",
                    "title": item.get("title", ""),
                    "url": url,
                    "description": item.get("body", ""),
                    "source": source,
                    "platform": "web"
                }
                articles.append(article)

            print(f"[ResourceDiscoveryService] Found {len(articles)} articles for: {query}")
            return articles

        except Exception as e:
            print(f"[ResourceDiscoveryService] Article search error: {e}")
            return self._fallback_article_results(query, max_results)

    def check_resource_relevance(self, resource: Dict, session_topic: str, main_topic: str) -> bool:
        """Check if a resource is relevant to the session topic using LLM.

        Args:
            resource: Resource dictionary with title and description
            session_topic: The specific topic being learned
            main_topic: The main learning topic

        Returns:
            True if resource is relevant, False otherwise
        """
        llm = self._get_llm_service()
        if not llm:
            # If LLM not available, assume relevant
            return True

        title = resource.get("title", "")
        description = resource.get("description", "")
        resource_type = resource.get("type", "resource")

        prompt = f"""Evaluate if this {resource_type} is relevant and useful for learning about "{session_topic}" (part of learning {main_topic}).

Resource Title: {title}
Description: {description[:300] if description else 'No description'}

Respond with ONLY "yes" or "no":
- "yes" if the resource directly teaches or explains the topic
- "no" if it's unrelated, tangential, entertainment-focused, or not educational

Answer:"""

        try:
            response = llm._call_llm(prompt, max_tokens=10).strip().lower()
            is_relevant = response.startswith("yes")
            if not is_relevant:
                print(f"[ResourceDiscoveryService] Filtered out irrelevant {resource_type}: {title[:50]}")
            return is_relevant
        except Exception as e:
            print(f"[ResourceDiscoveryService] Relevance check error: {e}")
            return True  # Default to keeping resource on error

    def find_resources_for_topic(
        self,
        main_topic: str,
        session_topic: str,
        num_videos: int = 2,
        num_articles: int = 1
    ) -> List[Dict]:
        """Find resources for a specific session topic.

        Args:
            main_topic: Main learning topic (e.g., "Python")
            session_topic: Specific session topic (e.g., "Python Functions")
            num_videos: Number of videos to find
            num_articles: Number of articles to find

        Returns:
            Combined list of video and article resources
        """
        resources = []

        # Search for videos (get extra to filter for relevance)
        video_query = f"{session_topic} tutorial"
        videos = self.search_youtube_videos(video_query, max_results=num_videos + 4)

        # Filter videos for relevance
        relevant_videos = []
        for video in videos:
            if len(relevant_videos) >= num_videos:
                break
            if self.check_resource_relevance(video, session_topic, main_topic):
                relevant_videos.append(video)
        resources.extend(relevant_videos)

        # Search for articles (get extra to filter for relevance)
        article_query = f"{session_topic} guide tutorial"
        articles = self.search_articles(article_query, max_results=num_articles + 4)

        # Filter articles for relevance
        relevant_articles = []
        for article in articles:
            if len(relevant_articles) >= num_articles:
                break
            if self.check_resource_relevance(article, session_topic, main_topic):
                relevant_articles.append(article)
        resources.extend(relevant_articles)

        return resources

    def score_video_quality(self, video: Dict) -> float:
        """Score a video for educational quality (0.0 to 1.0).

        Args:
            video: Video dictionary

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        title = video.get("title", "").lower()

        # Boost for educational keywords
        educational_keywords = ["tutorial", "explained", "learn", "beginner", "guide", "how to", "introduction"]
        for keyword in educational_keywords:
            if keyword in title:
                score += 0.1

        # Penalize clickbait
        clickbait_keywords = ["shocking", "won't believe", "gone wrong", "funny"]
        for keyword in clickbait_keywords:
            if keyword in title:
                score -= 0.2

        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, score))

    def score_article_quality(self, article: Dict) -> float:
        """Score an article for educational quality (0.0 to 1.0).

        Args:
            article: Article dictionary

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.5  # Base score

        source = article.get("source", "").lower()
        title = article.get("title", "").lower()

        # Boost for trusted sources
        trusted_sources = [
            "freecodecamp.org", "dev.to", "medium.com", "realpython.com",
            "digitalocean.com", "geeksforgeeks.org", "developer.mozilla.org",
            "docs.python.org", "w3schools.com"
        ]
        for trusted in trusted_sources:
            if trusted in source:
                score += 0.3
                break

        # Boost for educational keywords
        educational_keywords = ["tutorial", "guide", "learn", "introduction", "explained"]
        for keyword in educational_keywords:
            if keyword in title:
                score += 0.05

        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, score))

    def _fallback_youtube_results(self, query: str, max_results: int) -> List[Dict]:
        """Generate fallback YouTube search URLs."""
        encoded_query = quote_plus(query)
        return [{
            "type": "video",
            "title": f"Search YouTube: {query}",
            "url": f"https://www.youtube.com/results?search_query={encoded_query}",
            "duration": "",
            "channel": "",
            "views": "",
            "thumbnail": "",
            "platform": "youtube",
            "is_fallback": True
        }]

    def _fallback_article_results(self, query: str, max_results: int) -> List[Dict]:
        """Generate fallback article search URLs."""
        encoded_query = quote_plus(query)
        return [{
            "type": "article",
            "title": f"Search: {query}",
            "url": f"https://duckduckgo.com/?q={encoded_query}",
            "description": "Click to search for articles",
            "source": "duckduckgo.com",
            "platform": "web",
            "is_fallback": True
        }]


def get_resource_discovery_service() -> ResourceDiscoveryService:
    """Get the singleton resource discovery service instance.

    Returns:
        ResourceDiscoveryService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = ResourceDiscoveryService()
    return _service_instance
