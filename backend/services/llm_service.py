"""LLM service using OpenAI GPT-4.1."""

from openai import OpenAI
from backend.config import get_settings
from typing import List, Dict, Optional
import json

settings = get_settings()


class LLMService:
    """Service for interacting with OpenAI API."""

    def __init__(self):
        """Initialize OpenAI client."""
        api_key = settings.openai_api_key
        if not api_key or api_key == "":
            raise ValueError(f"OPENAI_API_KEY is empty or not set! Check backend/.env file")

        print(f"[LLMService] Initializing with OpenAI API key: {api_key[:20]}...")

        try:
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4.1"
            print(f"[LLMService] Successfully initialized OpenAI client with model: {self.model}")
        except Exception as e:
            print(f"[LLMService] ERROR initializing OpenAI client: {e}")
            raise

    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """Make a call to the OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def _extract_json(self, content: str) -> str:
        """Extract JSON from markdown code blocks if present."""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content

    def analyze_topic_scope(self, topic: str, proficiency_level: str) -> Dict:
        """Analyze a topic to determine its scope and key learning areas."""
        prompt = f"""Analyze the learning topic: {topic}

For a {proficiency_level} learner, provide:
1. A brief scope description (what this topic covers)
2. The key learning areas (main subtopics to master)
3. Estimated number of modules needed
4. Complexity level
5. Any prerequisite knowledge needed

Format your response as JSON:
{{
    "topic": "{topic}",
    "scope": "Brief description of what this topic covers",
    "key_areas": ["Area 1", "Area 2", "Area 3", ...],
    "estimated_modules": <number>,
    "complexity": "low|medium|high",
    "prerequisites_needed": ["Prerequisite 1", ...]
}}

Be practical and focus on what's actually needed for a {proficiency_level} learner."""

        try:
            content = self._call_llm(prompt, max_tokens=800)
            content = self._extract_json(content)
            result = json.loads(content)
            print(f"[LLMService] Analyzed topic scope: {len(result.get('key_areas', []))} key areas")
            return result
        except Exception as e:
            print(f"Error analyzing topic scope: {e}")
            return {
                "topic": topic,
                "scope": f"Introduction to {topic}",
                "key_areas": [f"{topic} Fundamentals", f"{topic} Core Concepts", f"Applied {topic}"],
                "estimated_modules": 5,
                "complexity": "medium",
                "prerequisites_needed": []
            }

    def generate_module_outline(self, topic: str, module_title: str, proficiency_level: str, module_number: int, total_modules: int) -> Dict:
        """Generate a detailed outline for a single curriculum module."""
        prompt = f"""Create a detailed module outline for:

Main Topic: {topic}
Module Title: {module_title}
Module Number: {module_number} of {total_modules}
Target Level: {proficiency_level}

Generate a module with:
- 2-3 learning objectives
- 3-5 subtopics (each becomes a study session)
- Realistic time estimates

Format as JSON:
{{
    "module_id": "m{module_number}",
    "title": "{module_title}",
    "description": "Brief overview of what this module covers",
    "duration_hours": <number>,
    "learning_objectives": ["Objective 1", "Objective 2"],
    "subtopics": [
        {{
            "title": "Subtopic Title",
            "description": "What will be covered in this session",
            "estimated_minutes": 30
        }}
    ],
    "prerequisites": []
}}

Make it practical and appropriate for a {proficiency_level} learner."""

        try:
            content = self._call_llm(prompt, max_tokens=1000)
            content = self._extract_json(content)
            result = json.loads(content)
            print(f"[LLMService] Generated module outline: {module_title} with {len(result.get('subtopics', []))} subtopics")
            return result
        except Exception as e:
            print(f"Error generating module outline: {e}")
            return {
                "module_id": f"m{module_number}",
                "title": module_title,
                "description": f"Introduction to {module_title}",
                "duration_hours": 2,
                "learning_objectives": [f"Understand {module_title} concepts", f"Apply {module_title} in practice"],
                "subtopics": [
                    {"title": f"{module_title} Basics", "description": "Foundational concepts", "estimated_minutes": 30},
                    {"title": f"{module_title} in Practice", "description": "Hands-on application", "estimated_minutes": 30}
                ],
                "prerequisites": [f"m{module_number-1}"] if module_number > 1 else []
            }

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
            content = self._call_llm(prompt, max_tokens=2000)
            print(f"[LLMService] Raw curriculum response length: {len(content)}")

            content = self._extract_json(content)
            curriculum = json.loads(content)
            print(f"[LLMService] Successfully parsed curriculum with {len(curriculum.get('modules', []))} modules")
            return curriculum

        except Exception as e:
            print(f"Error generating curriculum: {e}")
            print(f"Raw content: {content[:200] if 'content' in locals() else 'N/A'}...")
            return self._fallback_curriculum(topic)

    def get_resources_for_module(self, module_title: str, subtopics: List[str]) -> List[Dict]:
        """Generate specific, high-quality learning resources for a module."""
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
            content = self._call_llm(prompt, max_tokens=1000)
            content = self._extract_json(content)
            resources = json.loads(content)
            print(f"[LLMService] Successfully generated {len(resources)} resources")
            return resources

        except Exception as e:
            print(f"Error generating resources: {e}")
            return []

    def generate_quiz(self, module_title: str, subtopics: List[str], num_questions: int = 5) -> List[Dict]:
        """Generate quiz questions for a module."""
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
            content = self._call_llm(prompt, max_tokens=1500)
            content = self._extract_json(content)

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
            content = self._call_llm(prompt, max_tokens=1200)
            content = self._extract_json(content)
            questions = json.loads(content)
            print(f"[LLMService] Successfully generated {len(questions)} proficiency questions")
            return questions

        except Exception as e:
            print(f"Error generating proficiency questions: {e}")
            print(f"Raw content: {content[:200] if 'content' in locals() else 'N/A'}...")
            return self._fallback_proficiency_questions(topic)

    def generate_study_guide(self, module_title: str, subtopics: List[str]) -> str:
        """Generate a markdown study guide for a module."""
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
            content = self._call_llm(prompt, max_tokens=1000)
            return content

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
