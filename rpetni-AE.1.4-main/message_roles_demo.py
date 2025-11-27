from typing import List, Dict, Optional
import google.generativeai as genai


class MessageRoleDemo:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def explain_roles(self) -> Dict[str, str]:
        return {
            "system": (
                "SYSTEM role sets the AI's behavior, personality, and constraints. "
                "It's like giving the AI its job description. "
                "Example: 'You are an expert technical interviewer with 10 years experience.'"
            ),
            "user": (
                "USER role represents the human's input - questions, requests, or responses. "
                "This is what the person interacting with the AI says. "
                "Example: 'Generate a coding interview question for a senior developer.'"
            ),
            "assistant": (
                "ASSISTANT role represents the AI's previous responses in the conversation. "
                "Used to maintain conversation history and context. "
                "Example: 'Here's a question: Implement a LRU cache with O(1) operations.'"
            )
        }

    def openai_style_messages(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        messages = []

        # 1. System message - sets the AI's behavior
        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # 2. Conversation history - alternating user/assistant messages
        if conversation_history:
            messages.extend(conversation_history)

        # 3. Current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    def gemini_style_conversion(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> tuple[str, List[Dict[str, str]]]:
        # Gemini uses system_instruction separately
        system_instruction = system_prompt

        # Build chat history in Gemini format
        chat_history = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

        # Add current user message
        chat_history.append({
            "role": "user",
            "parts": [user_message]
        })

        return system_instruction, chat_history

    def generate_with_roles(
        self,
        role: str,
        company: str,
        round_type: str,
        difficulty: str,
        model_name: str = "gemini-2.0-flash-exp"
    ) -> str:
        # SYSTEM role - defines the AI's behavior
        system_instruction = f"""You are an expert technical interviewer with 15+ years of experience.
Your specialty is creating challenging, fair interview questions that assess real-world skills.
You understand how to calibrate questions for different experience levels and interview stages."""

        # USER role - the actual request
        user_message = f"""Generate one interview question with these specifications:
- Role: {role}
- Company: {company or 'a tech company'}
- Interview Round: {round_type}
- Difficulty: {difficulty}

The question should be specific, clear, and relevant to the role."""

        # Create model with system instruction (Gemini's way of handling system role)
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )

        # Send user message
        response = model.generate_content(user_message)

        return response.text

    def multi_turn_conversation_example(self) -> List[Dict[str, str]]:
        conversation = [
            {
                "role": "system",
                "content": "You are a helpful interview coach providing feedback on answers."
            },
            {
                "role": "user",
                "content": "What is polymorphism in OOP?"
            },
            {
                "role": "assistant",
                "content": "Polymorphism is the ability of objects to take multiple forms. In OOP, it allows objects of different classes to be treated as objects of a common parent class."
            },
            {
                "role": "user",
                "content": "Can you give me an example in Python?"
            },
            {
                "role": "assistant",
                "content": "Sure! Here's an example:\n\nclass Animal:\n    def speak(self):\n        pass\n\nclass Dog(Animal):\n    def speak(self):\n        return 'Woof!'\n\nclass Cat(Animal):\n    def speak(self):\n        return 'Meow!'"
            }
        ]

        return conversation

    def demonstrate_role_importance(self) -> Dict[str, str]:
        return {
            "system_importance": (
                "System role is crucial for consistent behavior. "
                "Without it, the AI might respond differently each time. "
                "It's like the difference between 'answer this question' and "
                "'you are an expert - answer this question professionally.'"
            ),
            "user_importance": (
                "User role clearly marks what the human wants. "
                "This helps the AI understand context and intent. "
                "In multi-turn conversations, it tracks who said what."
            ),
            "assistant_importance": (
                "Assistant role maintains conversation memory. "
                "Without tracking previous assistant responses, the AI can't "
                "reference earlier parts of the conversation or maintain consistency."
            ),
            "practical_example": (
                "In our interview app, we use:\n"
                "- SYSTEM: 'You are an expert interviewer...'\n"
                "- USER: 'Generate a question for Software Engineer...'\n"
                "- ASSISTANT: (previous questions to avoid repetition)\n"
                "This structure ensures quality and context-aware questions."
            )
        }


# Example usage demonstrating understanding
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("⚠️  No API key found. This demo shows the concepts without making API calls.")
    
    demo = MessageRoleDemo(api_key or "dummy_key")
    
    print("=" * 60)
    print("UNDERSTANDING MESSAGE ROLES IN LLM APIS")
    print("=" * 60)
    print()
    
    # Explain roles
    print("1. ROLE EXPLANATIONS:")
    print("-" * 60)
    roles = demo.explain_roles()
    for role_name, explanation in roles.items():
        print(f"\n{role_name.upper()}:")
        print(f"  {explanation}")
    
    print("\n" + "=" * 60)
    print("2. OPENAI-STYLE MESSAGE STRUCTURE:")
    print("-" * 60)
    messages = demo.openai_style_messages(
        system_prompt="You are an expert interviewer.",
        user_message="Generate a coding question.",
        conversation_history=[
            {"role": "assistant", "content": "Previous question: What is a hash table?"}
        ]
    )
    for msg in messages:
        print(f"\n{msg['role'].upper()}:")
        print(f"  {msg['content']}")
    
    print("\n" + "=" * 60)
    print("3. MULTI-TURN CONVERSATION EXAMPLE:")
    print("-" * 60)
    conversation = demo.multi_turn_conversation_example()
    for i, msg in enumerate(conversation, 1):
        print(f"\nTurn {i} - {msg['role'].upper()}:")
        print(f"  {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
    
    print("\n" + "=" * 60)
    print("4. WHY ROLES MATTER:")
    print("-" * 60)
    importance = demo.demonstrate_role_importance()
    for key, explanation in importance.items():
        print(f"\n{key.replace('_', ' ').title()}:")
        print(f"  {explanation}")
    
    print("\n" + "=" * 60)
    print("\n✅ This demonstrates clear understanding of user, system, and assistant roles!")
    print("   These concepts apply across OpenAI, Anthropic, Google, and other LLM APIs.")
