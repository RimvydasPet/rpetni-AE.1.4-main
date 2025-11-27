import os
from typing import Optional, Dict, Any, List, Tuple

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from prompt_strategies import get_prompt_by_strategy, get_available_strategies

DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

DEFAULT_GENERATION_CONFIG: dict[str, float | int] = {
    "temperature": 0.75,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 3000,  # Increased from 2048 to handle longer responses
}

# Default safety settings - block medium or higher probability of unsafe content
DEFAULT_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}



def _merge_generation_config(
    overrides: Optional[dict[str, float | int]] = None,
) -> dict[str, float | int]:
    config = DEFAULT_GENERATION_CONFIG.copy()
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                config[key] = value
    return config


def _extract_text_from_candidate(candidate) -> str:
    content = getattr(candidate, "content", None)
    if not content:
        return ""


def _extract_text_from_response(response) -> str:
    if not response:
        return ""
    try:
        quick_text = getattr(response, "text", None)
        if quick_text:
            text_value = quick_text.strip()
            if text_value:
                return text_value
    except ValueError:
        # Gemini raises when no valid Part exists—fall back to manual parsing.
        pass

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        candidate_text = _extract_text_from_candidate(candidate)
        if candidate_text:
            return candidate_text
    return ""


def validate_google_api_key(
    api_key: str,
    generation_config: Optional[dict[str, float | int]] = None,
    safety_settings: Optional[dict] = None,
) -> None:
    if not api_key or not api_key.strip():
        raise ValueError("GOOGLE_API_KEY missing. Provide it via .env before generating questions.")

    try:
        genai.configure(api_key=api_key)
        effective_config = _merge_generation_config(generation_config)

        effective_safety = safety_settings or DEFAULT_SAFETY_SETTINGS
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=effective_config,
            safety_settings=effective_safety,
        )
        model.count_tokens("ping")
    except Exception as exc:
        raise RuntimeError(f"GOOGLE_API_KEY validation failed: {exc}") from exc


def generate_question(
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
    api_key: str | None = None,
    generation_config: Optional[dict[str, float | int]] = None,
    safety_settings: Optional[dict] = None,
    prompt_strategy: str = "chain_of_thought",
) -> str:
    # Debug: Print the API key status (first few characters for security)
    print(f"API Key provided: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key starts with: {api_key[:5]}...")

    if not api_key:
        raise ValueError("GOOGLE_API_KEY missing. Please provide it via the .env file or settings.")

    # Generate using Gemini
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        effective_config = _merge_generation_config(generation_config)
        effective_safety = safety_settings or DEFAULT_SAFETY_SETTINGS
        
        # Initialize the model
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=effective_config,
            safety_settings=effective_safety,
        )
        
        # Prepare the prompt using the selected strategy
        print(f"Using prompt strategy: {prompt_strategy}")
        prompt = get_prompt_by_strategy(
            strategy=prompt_strategy,
            role=role,
            company=company,
            round_type=round_type,
            difficulty=difficulty,
            previous_questions=previous_questions,
        )
            
        print(f"Sending request to Gemini API with {prompt_strategy} strategy...")
        response = model.generate_content(prompt)
        print(f"Received response: {response}")
        
        question = _extract_text_from_response(response)
        print(f"Extracted question: {question}")
        
        # Return the question if we got one
        if question:
            # Clean up the question
            question = question.strip()
            
            # Remove common prefixes that LLMs sometimes add
            prefixes_to_remove = [
                "**Question:**",
                "**Question**:",
                "Question:",
                "**Q:**",
                "Q:",
                "Interview Question:",
                "**Interview Question:**",
            ]
            
            for prefix in prefixes_to_remove:
                if question.startswith(prefix):
                    question = question[len(prefix):].strip()
                    break
            
            # Ensure question ends with a question mark
            if not question.endswith("?"):
                question += "?"
                
            print(f"Returning generated question: {question}")
            return question
        # Get detailed error information
        finish_reasons = []
        for candidate in getattr(response, "candidates", []):
            finish_reason = getattr(candidate, "finish_reason", "")
            if finish_reason:
                finish_reasons.append(str(finish_reason))
                
            # Check for safety ratings
            safety_ratings = getattr(candidate, "safety_ratings", [])
            for rating in safety_ratings:
                if getattr(rating, "blocked", False):
                    finish_reasons.append(f"BLOCKED: {getattr(rating, 'category', 'Unknown')}")
        
        finish_reason_str = ", ".join(finish_reasons) if finish_reasons else "No finish reason provided"
        print(f"Generation failed. Finish reasons: {finish_reason_str}")
        
        # Check for MAX_TOKENS issue
        if "MAX_TOKENS" in finish_reason_str.upper() or "2" in finish_reason_str:
            print("Hit max tokens limit")
            raise RuntimeError(
                "Response exceeded token limit. "
                "Try increasing 'Max Tokens' in the LLM Generation Settings (recommended: 1024-2048)."
            )
        
        # If we have safety issues, provide clear guidance
        if any(r in finish_reason_str.upper() for r in ["SAFETY", "BLOCKED"]):
            print("Content blocked by safety filters")
            raise RuntimeError(
                "Content blocked by Gemini safety filters. "
                "Try adjusting your safety settings to 'Block None' or 'Block Few' in the app settings."
            )
            
        # For other errors, provide more detailed information
        error_details = {
            "role": role,
            "company": company,
            "round_type": round_type,
            "difficulty": difficulty,
            "finish_reasons": finish_reasons,
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
        print(f"Error details: {error_details}")
        
        raise RuntimeError(
            "Gemini returned an empty or invalid response. "
            f"Finish reasons: {finish_reason_str}"
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini question generation failed: {exc}") from exc
