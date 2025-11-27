"""Resource discovery tools for ADK agents.

These tools allow agents to search for real YouTube videos and articles.
"""

from typing import Dict, List
from backend.services.resource_discovery_service import get_resource_discovery_service


def search_youtube(query: str, max_results: int = 5) -> Dict:
    """Search YouTube for educational videos.

    Args:
        query: Search query for finding videos (e.g., "Python functions tutorial")
        max_results: Maximum number of video results to return (default: 5)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if search succeeded
        - videos: List of video objects with title, url, duration, channel, etc.
        - error: Error message if search failed
    """
    try:
        service = get_resource_discovery_service()
        videos = service.search_youtube_videos(query, max_results=max_results)
        return {
            "success": True,
            "videos": videos,
            "count": len(videos)
        }
    except Exception as e:
        return {
            "success": False,
            "videos": [],
            "error": str(e)
        }


def search_articles(query: str, max_results: int = 5) -> Dict:
    """Search for educational articles (excludes Wikipedia).

    Uses DuckDuckGo to find articles from quality sources like dev.to,
    Medium, FreeCodeCamp, official documentation, etc.

    Args:
        query: Search query for finding articles (e.g., "Python functions guide")
        max_results: Maximum number of article results to return (default: 5)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if search succeeded
        - articles: List of article objects with title, url, description, source
        - error: Error message if search failed
    """
    try:
        service = get_resource_discovery_service()
        articles = service.search_articles(query, max_results=max_results)
        return {
            "success": True,
            "articles": articles,
            "count": len(articles)
        }
    except Exception as e:
        return {
            "success": False,
            "articles": [],
            "error": str(e)
        }
