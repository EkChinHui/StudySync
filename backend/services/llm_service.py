"""LLM service using Anthropic Claude."""

from anthropic import Anthropic
from backend.config import get_settings
from typing import List, Dict, Optional
import json

settings = get_settings()


class LLMService:
    """Service for interacting with Anthropic Claude API."""

    def __init__(self):
        """Initialize Anthropic client."""
        api_key = settings.anthropic_api_key
        if not api_key or api_key == "":
            raise ValueError(f"ANTHROPIC_API_KEY is empty or not set! Check backend/.env file")

        print(f"[LLMService] Initializing with API key: {api_key[:20]}...")

        try:
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-sonnet-4-5-20250929"
            # self.model = "claude-haiku-4-5-20251001"
            print(f"[LLMService] Successfully initialized Anthropic client")
        except Exception as e:
            print(f"[LLMService] ERROR initializing Anthropic client: {e}")
            raise

    def generate_curriculum(self, topic: str, proficiency_level: str, commitment_level: str, duration_weeks: Optional[float] = None) -> Dict:
        """Generate a learning curriculum for the given topic."""
        
        duration_context = ""
        if duration_weeks:
            duration_context = f"""
IMPORTANT DURATION CONSTRAINT:
The user has only {duration_weeks} weeks available.
You MUST scale the curriculum to fit exactly within {duration_weeks} weeks.
- If duration is short (e.g. < 2 weeks), create fewer modules and focus ONLY on essentials.
- Adjust 'duration_hours' for each module to fit the timeline.
- Do NOT generate a generic 4-8 week curriculum.
"""

        prompt = f"""Generate a detailed learning curriculum for the topic: {topic}

User Profile:
- Proficiency Level: {proficiency_level}
- Commitment Level: {commitment_level} (light=2-4hrs/week, moderate=5-8hrs/week, intensive=10+hrs/week)
{duration_context}

Please create a structured curriculum. Each module should include:
- A clear title
- Learning objectives (2-3 points)
- Estimated duration in hours
- 3-5 subtopics. Each subtopic will become a study session.

Format your response as JSON with this structure:
{{
  "topic": "{topic}",
  "total_duration_weeks": <number>,
  "modules": [
    {{
      "module_id": "m1",
      "title": "Module Title",
      "duration_hours": <number>,
      "learning_objectives": ["objective1", "objective2"],
      "subtopics": [
        {{
          "title": "Subtopic Title",
          "description": "Brief description of what will be covered in this session (1 sentence)",
          "estimated_minutes": 30
        }}
      ],
      "prerequisites": []
    }}
  ]
}}

Keep it practical and focused on the essentials for a {proficiency_level} learner."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            print(f"[LLMService] Raw curriculum response length: {len(content)}")

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Parse JSON from response
            curriculum = json.loads(content)
            print(f"[LLMService] Successfully parsed curriculum with {len(curriculum.get('modules', []))} modules")
            return curriculum

        except Exception as e:
            print(f"Error generating curriculum: {e}")
            print(f"Raw content: {content[:200] if 'content' in locals() else 'N/A'}...")
            # Return fallback curriculum
            return self._fallback_curriculum(topic)

    def get_resources_for_module(self, module_title: str, subtopics: List[str]) -> List[Dict]:
        """Generate specific, high-quality learning resources for a module."""
        # Handle if subtopics are objects (dicts) or strings
        subtopic_names = []
        for s in subtopics:
            if isinstance(s, dict):
                subtopic_names.append(s.get("title", ""))
            else:
                subtopic_names.append(str(s))

        prompt = f"""Find 3-5 specific, high-quality learning resources for:
        
Module: {module_title}
Topics: {', '.join(subtopic_names)}

Please provide specific, real URLs to high-quality content.
IMPORTANT PREFERENCE:
- Prioritize SHORT videos (5-15 minutes) that cover specific concepts.
- Avoid 2+ hour long courses unless absolutely necessary.
- Include official documentation and short articles.

Format as a JSON array of objects:
[
  {{
    "type": "video|article|documentation|interactive",
    "title": "Specific Title of Resource",
    "url": "https://specific-url.com/...",
    "description": "Brief description of what this covers (e.g. '10 min video on loops')"
  }}
]

IMPORTANT:
- Do NOT use generic search URLs (e.g., google.com/search?q=...)
- Provide REAL, specific links that are likely to exist and be high quality.
- If you are unsure of a specific URL, provide a very specific search query URL as a fallback, but prioritize direct links."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            resources = json.loads(content)
            print(f"[LLMService] Successfully generated {len(resources)} resources")
            return resources

        except Exception as e:
            print(f"Error generating resources: {e}")
            return []

    def generate_quiz(self, module_title: str, subtopics: List[str], num_questions: int = 5) -> List[Dict]:
        """Generate quiz questions for a module."""
        # Handle if subtopics are objects (dicts) or strings
        subtopic_names = []
        for s in subtopics:
            if isinstance(s, dict):
                subtopic_names.append(s.get("title", ""))
            else:
                subtopic_names.append(str(s))

        prompt = f"""Create {num_questions} multiple-choice quiz questions for a learning module.

Module: {module_title}
Topics covered: {', '.join(subtopic_names)}

IMPORTANT:
- Do NOT include code snippets in questions (they break JSON parsing)
- Keep questions conceptual and text-based only
- Use simple, clear language
- Avoid special characters like quotes and backslashes in questions

For each question, provide:
- The question text (NO code snippets)
- 4 answer options (A, B, C, D)
- The correct answer (letter)
- A brief explanation

Format as valid JSON array with proper escaping:
[
  {{
    "question": "What is the primary characteristic of this concept?",
    "options": {{
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    }},
    "correct_answer": "B",
    "explanation": "Brief explanation why B is correct"
  }}
]

Make questions practical and test understanding, not just memorization."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            try:
                questions = json.loads(content)
                print(f"[LLMService] Successfully generated {len(questions)} quiz questions")
                return questions
            except json.JSONDecodeError as json_err:
                print(f"JSON decode error: {json_err}")
                print(f"Attempting to fix malformed JSON...")
                return self._fallback_quiz()

        except Exception as e:
            print(f"Error generating quiz: {e}")
            print(f"Raw content: {content[:200] if 'content' in locals() else 'N/A'}...")
            return self._fallback_quiz()

    def generate_proficiency_questions(self, topic: str) -> List[Dict]:
        """Generate adaptive proficiency assessment questions."""
        prompt = f"""Create 5 proficiency assessment questions for the topic: {topic}

These questions should help determine if the learner is a beginner, intermediate, or advanced.
Start with basic questions and increase in difficulty.

Format as JSON array:
[
  {{
    "question": "Question text?",
    "type": "multiple_choice",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "difficulty": "beginner|intermediate|advanced"
  }}
]

Make questions practical and assess real understanding."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            questions = json.loads(content)
            print(f"[LLMService] Successfully generated {len(questions)} proficiency questions")
            return questions

        except Exception as e:
            print(f"Error generating proficiency questions: {e}")
            print(f"Raw content: {content[:200] if 'content' in locals() else 'N/A'}...")
            return self._fallback_proficiency_questions(topic)

    def generate_study_guide(self, module_title: str, subtopics: List[str]) -> str:
        """Generate a markdown study guide for a module."""
        # Handle if subtopics are objects (dicts) or strings
        subtopic_names = []
        for s in subtopics:
            if isinstance(s, dict):
                subtopic_names.append(s.get("title", ""))
            else:
                subtopic_names.append(str(s))

        prompt = f"""Create a concise study guide for:

Module: {module_title}
Topics: {', '.join(subtopic_names)}

Format as markdown with:
- Key concepts and definitions
- Important points to remember
- Practical examples
- Quick tips for learning

Keep it under 500 words and actionable."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Error generating study guide: {e}")
            return f"# {module_title}\n\nStudy guide generation failed. Please refer to module resources."

    def _fallback_curriculum(self, topic: str) -> Dict:
        """Fallback curriculum if API fails."""
        return {
            "topic": topic,
            "total_duration_weeks": 4,
            "modules": [
                {
                    "module_id": "m1",
                    "title": f"Introduction to {topic}",
                    "duration_hours": 4,
                    "learning_objectives": ["Understand basic concepts", "Build foundational knowledge"],
                    "subtopics": ["Fundamentals", "Core Concepts"],
                    "prerequisites": []
                }
            ]
        }

    def _fallback_quiz(self) -> List[Dict]:
        """Fallback quiz if API fails."""
        return [
            {
                "question": "Sample question - quiz generation temporarily unavailable",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "This is a placeholder question"
            }
        ]

    def _fallback_proficiency_questions(self, topic: str) -> List[Dict]:
        """Fallback proficiency questions."""
        return [
            {
                "question": f"How familiar are you with {topic}?",
                "type": "multiple_choice",
                "options": [
                    "Never heard of it",
                    "Heard of it but never used it",
                    "Some basic experience",
                    "Regular user with good understanding"
                ],
                "difficulty": "beginner"
            }
        ]
