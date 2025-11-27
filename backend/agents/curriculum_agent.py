"""Curriculum Agent - Generates learning curriculum and finds resources."""

from typing import Dict, List, Optional
from backend.services.llm_service import LLMService
import httpx


class CurriculumAgent:
    """Agent responsible for curriculum generation and resource curation."""

    def __init__(self):
        """Initialize the agent."""
        self.llm_service = LLMService()

    async def run(self, topic: str, user_profile: Dict, duration_weeks: Optional[float] = None) -> Dict:
        """
        Generate curriculum for the topic based on user profile.

        Args:
            topic: Learning topic
            user_profile: User profile from UserProfilerAgent
            duration_weeks: Optional duration constraint in weeks

        Returns:
            Curriculum with modules and resources
        """
        # Generate curriculum structure using LLM
        curriculum = self.llm_service.generate_curriculum(
            topic=topic,
            proficiency_level=user_profile["proficiency_level"],
            commitment_level=user_profile["commitment_level"],
            duration_weeks=duration_weeks
        )

        # Find resources for each module
        for module in curriculum.get("modules", []):
            resources = await self._find_resources(
                topic=topic,
                subtopics=module.get("subtopics", [])
            )
            module["resources"] = resources

        return curriculum

    async def _find_resources(self, topic: str, subtopics: List[str]) -> List[Dict]:
        """
        Find learning resources for the topic.
        Uses LLM to find specific, high-quality resources.
        """
        # Get specific resources from LLM
        resources = self.llm_service.get_resources_for_module(
            module_title=topic,
            subtopics=subtopics
        )

        # Add a fallback search query if no resources found or as an extra option
        if not resources:
            resources.append({
                "type": "search_query",
                "title": f"Search: {topic} tutorial",
                "url": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial",
                "quality_score": 0.8,
                "is_generated": False
            })
        
        # Always add official documentation search as a backup
        resources.append({
            "type": "documentation",
            "title": f"Find Official Documentation",
            "url": f"https://www.google.com/search?q={topic.replace(' ', '+')}+official+documentation",
            "quality_score": 0.9,
            "is_generated": False
        })

        
        # For POC, also generate a study guide
        if len(subtopics) > 0:
            # Extract subtopic titles if they are dicts
            subtopic_titles = []
            for s in subtopics[:2]:
                if isinstance(s, dict):
                    subtopic_titles.append(s.get("title", ""))
                else:
                    subtopic_titles.append(str(s))
            
            study_guide = self.llm_service.generate_study_guide(
                module_title=f"{topic} - {', '.join(subtopic_titles)}",
                subtopics=subtopics
            )
            resources.append({
                "type": "study_guide",
                "title": "AI-Generated Study Guide",
                "content": study_guide,
                "quality_score": 0.7,
                "is_generated": True
            })

        return resources

    def _search_youtube(self, query: str, api_key: str) -> List[Dict]:
        """
        Search YouTube for educational videos.
        Placeholder for future implementation with YouTube Data API.
        """
        # Would use YouTube Data API here
        # For now, return search URL
        return []
