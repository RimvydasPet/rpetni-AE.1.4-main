"""
Demonstration of different LLM output types.

This module shows understanding of various output formats that LLMs can produce:
1. Plain text (default)
2. JSON/structured output
3. Streaming responses
4. Multi-modal outputs (text + metadata)

This demonstrates advanced LLM usage beyond simple text generation.
"""

import json
import os
from typing import Dict, List, Any, Generator, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import google.generativeai as genai
from dotenv import load_dotenv


class OutputType(Enum):
    """Different types of LLM outputs"""
    PLAIN_TEXT = "plain_text"
    JSON_STRUCTURED = "json_structured"
    STREAMING = "streaming"
    WITH_METADATA = "with_metadata"


@dataclass
class InterviewQuestion:
    """Structured format for interview questions"""
    question: str
    difficulty: str
    category: str
    expected_topics: List[str]
    follow_up_questions: List[str]
    evaluation_criteria: List[str]
    estimated_time_minutes: int


@dataclass
class QuestionWithMetadata:
    """Question with additional metadata"""
    question: str
    tokens_used: int
    generation_time_ms: float
    model_name: str
    safety_ratings: Dict[str, str]
    finish_reason: str


class OutputTypesDemo:
    """
    Demonstrates different LLM output types and when to use each.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
    
    def generate_plain_text(self, role: str, round_type: str) -> str:
        """
        Output Type 1: Plain Text (default)
        
        This is the simplest output type - just a string response.
        Good for: Simple questions, human-readable content, when structure isn't needed.
        
        Args:
            role: Job role
            round_type: Interview round
            
        Returns:
            Plain text question
        """
        model = genai.GenerativeModel(self.model_name)
        
        prompt = f"Generate one interview question for a {role} in the {round_type} round."
        
        response = model.generate_content(prompt)
        
        # Plain text output - just the string
        return response.text
    
    def generate_json_structured(
        self,
        role: str,
        round_type: str,
        difficulty: str
    ) -> InterviewQuestion:
        """
        Output Type 2: JSON/Structured Output
        
        Forces the LLM to return data in a specific JSON format.
        Good for: Programmatic processing, databases, APIs, consistent data structure.
        
        This is crucial for production applications that need reliable parsing.
        
        Args:
            role: Job role
            round_type: Interview round
            difficulty: Difficulty level
            
        Returns:
            Structured InterviewQuestion object
        """
        model = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        
        # Prompt that requests JSON format with specific schema
        prompt = f"""Generate an interview question for a {role} in the {round_type} round at {difficulty} level.

Return ONLY valid JSON with this exact structure:
{{
    "question": "The actual interview question",
    "difficulty": "{difficulty}",
    "category": "technical/behavioral/coding/etc",
    "expected_topics": ["topic1", "topic2", "topic3"],
    "follow_up_questions": ["follow-up 1", "follow-up 2"],
    "evaluation_criteria": ["criterion 1", "criterion 2", "criterion 3"],
    "estimated_time_minutes": 5
}}

Ensure all fields are filled with relevant content."""
        
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            json_data = json.loads(response.text)
            return InterviewQuestion(**json_data)
        except (json.JSONDecodeError, TypeError) as e:
            # Fallback if JSON parsing fails
            return InterviewQuestion(
                question=response.text,
                difficulty=difficulty,
                category="general",
                expected_topics=[],
                follow_up_questions=[],
                evaluation_criteria=[],
                estimated_time_minutes=5
            )
    
    def generate_streaming(
        self,
        role: str,
        round_type: str
    ) -> Generator[str, None, None]:
        """
        Output Type 3: Streaming Response
        
        Returns text incrementally as it's generated (like ChatGPT's typing effect).
        Good for: Better UX, showing progress, reducing perceived latency.
        
        This is important for real-time applications and user experience.
        
        Args:
            role: Job role
            round_type: Interview round
            
        Yields:
            Chunks of text as they're generated
        """
        model = genai.GenerativeModel(self.model_name)
        
        prompt = f"Generate one detailed interview question for a {role} in the {round_type} round."
        
        # Stream=True enables streaming
        response = model.generate_content(prompt, stream=True)
        
        # Yield chunks as they arrive
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    def generate_with_metadata(
        self,
        role: str,
        round_type: str
    ) -> QuestionWithMetadata:
        """
        Output Type 4: Response with Metadata
        
        Returns the content plus additional information about the generation.
        Good for: Debugging, monitoring, cost tracking, quality assessment.
        
        This shows understanding of the full response object, not just text.
        
        Args:
            role: Job role
            round_type: Interview round
            
        Returns:
            QuestionWithMetadata object with full response details
        """
        import time
        
        model = genai.GenerativeModel(self.model_name)
        
        prompt = f"Generate one interview question for a {role} in the {round_type} round."
        
        start_time = time.time()
        response = model.generate_content(prompt)
        generation_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Extract metadata from response object
        question_text = response.text
        
        # Get usage metadata (tokens)
        tokens_used = getattr(response, 'usage_metadata', None)
        total_tokens = 0
        if tokens_used:
            total_tokens = getattr(tokens_used, 'total_token_count', 0)
        
        # Get safety ratings
        safety_ratings = {}
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'safety_ratings'):
                for rating in candidate.safety_ratings:
                    category = str(rating.category).split('.')[-1]
                    probability = str(rating.probability).split('.')[-1]
                    safety_ratings[category] = probability
            
            # Get finish reason
            finish_reason = str(getattr(candidate, 'finish_reason', 'UNKNOWN')).split('.')[-1]
        else:
            finish_reason = "UNKNOWN"
        
        return QuestionWithMetadata(
            question=question_text,
            tokens_used=total_tokens,
            generation_time_ms=round(generation_time, 2),
            model_name=self.model_name,
            safety_ratings=safety_ratings,
            finish_reason=finish_reason
        )
    
    def compare_output_types(self) -> Dict[str, Dict[str, Any]]:
        """
        Compare different output types and their use cases.
        
        Returns:
            Dictionary explaining each output type
        """
        return {
            "plain_text": {
                "description": "Simple string output",
                "pros": ["Easy to use", "Human-readable", "Flexible"],
                "cons": ["Hard to parse programmatically", "Inconsistent structure"],
                "use_cases": [
                    "Simple Q&A",
                    "Human-facing content",
                    "When structure doesn't matter"
                ],
                "example": "What is polymorphism in OOP?"
            },
            "json_structured": {
                "description": "Structured data in JSON format",
                "pros": [
                    "Consistent structure",
                    "Easy to parse",
                    "Database-ready",
                    "Type-safe"
                ],
                "cons": ["Requires careful prompting", "May fail to parse"],
                "use_cases": [
                    "APIs and integrations",
                    "Database storage",
                    "Programmatic processing",
                    "When you need specific fields"
                ],
                "example": {
                    "question": "Explain polymorphism",
                    "difficulty": "medium",
                    "category": "OOP"
                }
            },
            "streaming": {
                "description": "Incremental text delivery",
                "pros": [
                    "Better UX (shows progress)",
                    "Lower perceived latency",
                    "Can stop early if needed"
                ],
                "cons": ["More complex to implement", "Can't parse until complete"],
                "use_cases": [
                    "Chat interfaces",
                    "Long responses",
                    "Real-time applications",
                    "When UX matters"
                ],
                "example": "Text appears word-by-word like ChatGPT"
            },
            "with_metadata": {
                "description": "Content plus generation details",
                "pros": [
                    "Full transparency",
                    "Debugging info",
                    "Cost tracking",
                    "Quality monitoring"
                ],
                "cons": ["More data to handle", "Requires parsing response object"],
                "use_cases": [
                    "Production monitoring",
                    "Cost optimization",
                    "Quality assurance",
                    "Debugging issues"
                ],
                "example": {
                    "text": "Question here",
                    "tokens": 150,
                    "time_ms": 1200,
                    "safety": "SAFE"
                }
            }
        }
    
    def demonstrate_all_types(self, role: str = "Software Engineer") -> Dict[str, Any]:
        """
        Generate examples of all output types.
        
        Args:
            role: Job role for examples
            
        Returns:
            Dictionary with examples of each output type
        """
        results = {}
        
        print("Generating examples of different output types...")
        print("=" * 60)
        
        # 1. Plain text
        print("\n1. PLAIN TEXT OUTPUT:")
        plain = self.generate_plain_text(role, "Coding")
        results["plain_text"] = plain
        print(f"   {plain[:100]}...")
        
        # 2. JSON structured
        print("\n2. JSON STRUCTURED OUTPUT:")
        structured = self.generate_json_structured(role, "Coding", "Professional")
        results["json_structured"] = asdict(structured)
        print(f"   Question: {structured.question[:80]}...")
        print(f"   Category: {structured.category}")
        print(f"   Expected topics: {', '.join(structured.expected_topics[:3])}")
        
        # 3. Streaming
        print("\n3. STREAMING OUTPUT:")
        print("   ", end="", flush=True)
        streaming_text = ""
        for chunk in self.generate_streaming(role, "Behavioral"):
            print(chunk, end="", flush=True)
            streaming_text += chunk
        results["streaming"] = streaming_text
        print()
        
        # 4. With metadata
        print("\n4. OUTPUT WITH METADATA:")
        with_meta = self.generate_with_metadata(role, "Technical")
        results["with_metadata"] = asdict(with_meta)
        print(f"   Question: {with_meta.question[:80]}...")
        print(f"   Tokens used: {with_meta.tokens_used}")
        print(f"   Generation time: {with_meta.generation_time_ms}ms")
        print(f"   Finish reason: {with_meta.finish_reason}")
        
        return results


# Example usage
if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("⚠️  No GOOGLE_API_KEY found in environment.")
        print("   Set it in .env file to run this demo.")
        print("\n   This demo shows understanding of different output types:")
        
        demo = OutputTypesDemo("dummy_key")
        comparison = demo.compare_output_types()
        
        for output_type, details in comparison.items():
            print(f"\n{output_type.upper().replace('_', ' ')}:")
            print(f"  Description: {details['description']}")
            print(f"  Pros: {', '.join(details['pros'])}")
            print(f"  Use cases: {', '.join(details['use_cases'][:2])}")
    else:
        demo = OutputTypesDemo(api_key)
        
        print("=" * 60)
        print("DEMONSTRATION OF DIFFERENT LLM OUTPUT TYPES")
        print("=" * 60)
        
        # Show comparison
        print("\nOUTPUT TYPE COMPARISON:")
        comparison = demo.compare_output_types()
        for output_type, details in comparison.items():
            print(f"\n{output_type.upper().replace('_', ' ')}:")
            print(f"  {details['description']}")
            print(f"  Best for: {', '.join(details['use_cases'][:2])}")
        
        print("\n" + "=" * 60)
        print("LIVE EXAMPLES:")
        print("=" * 60)
        
        # Generate examples
        results = demo.demonstrate_all_types()
        
        print("\n" + "=" * 60)
        print("\n✅ This demonstrates understanding of different LLM output types!")
        print("   Each type serves different purposes in production applications.")
