from typing import Optional


def zero_shot_prompt(
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
) -> str:
    prior_list = "\n".join(f"- {q}" for q in (previous_questions or [])) or "None"
    
    return f"""Generate a single interview question for the following position:

Role: {role}
Company: {company or 'a company'}
Interview Round: {round_type}
Difficulty Level: {difficulty}

Previously asked questions (avoid repetition):
{prior_list}

Generate exactly ONE challenging and relevant interview question.

Question:"""


def few_shot_prompt(
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
) -> str:
    prior_list = "\n".join(f"- {q}" for q in (previous_questions or [])) or "None"
    
    if round_type.lower() == "coding":
        examples = """
Example 1:
Role: Software Engineer
Question: "Implement a function to find the longest palindromic substring in a given string. What's the time complexity of your solution?"

Example 2:
Role: Backend Developer
Question: "Design a rate limiter for an API that handles 10,000 requests per second. Explain your approach and trade-offs."

Example 3:
Role: Full Stack Developer
Question: "How would you optimize a slow database query that joins three tables with millions of rows each?"
"""
    elif round_type.lower() == "behavioral":
        examples = """
Example 1:
Role: Product Manager
Question: "Tell me about a time when you had to make a difficult decision with incomplete information. How did you approach it?"

Example 2:
Role: Team Lead
Question: "Describe a situation where you had to give constructive feedback to a team member who wasn't meeting expectations."

Example 3:
Role: Software Engineer
Question: "Can you share an example of when you disagreed with your manager's technical decision? How did you handle it?"
"""
    else:
        examples = """
Example 1:
Role: Data Scientist
Question: "Explain the bias-variance tradeoff and how it impacts model selection in machine learning."

Example 2:
Role: DevOps Engineer
Question: "How would you design a CI/CD pipeline for a microservices architecture with 20+ services?"

Example 3:
Role: Security Engineer
Question: "What are the key differences between symmetric and asymmetric encryption, and when would you use each?"
"""
    
    return f"""Here are examples of high-quality interview questions:
{examples}

Now generate a similar question for:
Role: {role}
Company: {company or 'a company'}
Interview Round: {round_type}
Difficulty Level: {difficulty}

Previously asked questions (avoid these):
{prior_list}

Generate exactly ONE interview question following the style and quality of the examples above.

Question:"""


def chain_of_thought_prompt(
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
) -> str:
    prior_list = "\n".join(f"- {q}" for q in (previous_questions or [])) or "None"
    
    return f"""You need to generate an interview question. Let's think through this step by step:

Step 1: Analyze the role and requirements
- Role: {role}
- Company: {company or 'a company'}
- Interview Round: {round_type}
- Difficulty Level: {difficulty}

Step 2: Consider what skills are most important for this role
Think about: What are the key competencies needed for a {role}?

Step 3: Determine the appropriate question type
For {round_type} round at {difficulty} level, what type of question would best assess the candidate?

Step 4: Review previously asked questions to avoid repetition
{prior_list}

Step 5: Craft a question that:
- Tests relevant skills for the role
- Matches the difficulty level
- Is appropriate for the {round_type} round
- Doesn't repeat previous questions
- Encourages detailed, thoughtful responses

Now, based on this reasoning, generate exactly ONE interview question:

Question:"""


def role_based_prompt(
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
) -> str:
    prior_list = "\n".join(f"- {q}" for q in (previous_questions or [])) or "None"
    
    return f"""You are a senior technical recruiter with 15+ years of experience at top tech companies like Google, Meta, and Amazon. You've conducted over 5,000 interviews and have deep expertise in assessing candidates for technical roles.

Your task is to create an interview question that will effectively evaluate a candidate applying for:

Position: {role}
Company: {company or 'a company'}
Interview Stage: {round_type}
Candidate Level: {difficulty}

As an expert interviewer, you know that great questions should:
- Reveal the candidate's depth of knowledge
- Allow for follow-up discussions
- Differentiate between good and exceptional candidates
- Be fair and unbiased
- Relate to real-world scenarios

Questions already asked in this interview (avoid similar topics):
{prior_list}

Drawing on your extensive experience, craft exactly ONE interview question that will help identify the best candidate for this role.

Question:"""


def structured_output_prompt(
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
) -> str:
    prior_list = "\n".join(f"- {q}" for q in (previous_questions or [])) or "None"
    
    return f"""Generate an interview question with the following specifications:

TARGET ROLE: {role}
COMPANY: {company or 'a company'}
INTERVIEW ROUND: {round_type}
DIFFICULTY: {difficulty}

REQUIREMENTS:
1. The question must be relevant to the {role} position
2. It should match the {difficulty} difficulty level
3. It must be appropriate for the {round_type} interview round
4. It should encourage detailed responses (not yes/no questions)
5. It must be different from these previously asked questions:
{prior_list}

QUALITY CRITERIA:
- Clarity: The question should be unambiguous
- Relevance: Directly related to job responsibilities
- Depth: Should assess understanding, not just memorization
- Practicality: Related to real-world scenarios when possible

OUTPUT FORMAT:
Provide only the interview question, nothing else. The question should be:
- One clear, focused question (may include follow-up parts)
- Properly punctuated
- Professional in tone

Question:"""


def socratic_prompt(
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
) -> str:
    prior_list = "\n".join(f"- {q}" for q in (previous_questions or [])) or "None"
    
    return f"""Let's create an excellent interview question by answering these guiding questions:

Q1: What is the role we're interviewing for?
A1: {role}

Q2: What are the core competencies required for a {role}?
A2: [Consider technical skills, soft skills, and domain knowledge]

Q3: What interview round is this?
A3: {round_type}

Q4: What specific skills should the {round_type} round assess?
A4: [Think about what this round uniquely evaluates]

Q5: What difficulty level are we targeting?
A5: {difficulty}

Q6: How should questions differ between difficulty levels?
A6: [Consider complexity, depth, and expected experience]

Q7: What questions have already been asked?
A7: {prior_list}

Q8: What topics or skills haven't been covered yet?
A8: [Identify gaps in the interview coverage]

Q9: What real-world challenges does a {role} at {company or 'a company'} face?
A9: [Think about practical, job-relevant scenarios]

Q10: Based on all these considerations, what single question would best assess the candidate?

Generate exactly ONE interview question:

Question:"""


# Dictionary mapping strategy names to their functions
PROMPT_STRATEGIES = {
    "zero_shot": {
        "name": "Zero-Shot Prompting",
        "description": "Direct instruction without examples - simple and straightforward",
        "function": zero_shot_prompt,
    },
    "few_shot": {
        "name": "Few-Shot Learning",
        "description": "Provides examples to guide the model's output style and quality",
        "function": few_shot_prompt,
    },
    "chain_of_thought": {
        "name": "Chain-of-Thought (CoT)",
        "description": "Encourages step-by-step reasoning for more thoughtful questions",
        "function": chain_of_thought_prompt,
    },
    "role_based": {
        "name": "Role-Based Prompting",
        "description": "Assigns expert persona (senior recruiter) for specialized perspective",
        "function": role_based_prompt,
    },
    "structured_output": {
        "name": "Structured Output",
        "description": "Requests specific format and quality criteria for consistency",
        "function": structured_output_prompt,
    },
    "socratic": {
        "name": "Socratic Method",
        "description": "Uses guiding questions to lead the model to better outputs",
        "function": socratic_prompt,
    },
}


def get_prompt_by_strategy(
    strategy: str,
    role: str,
    company: str,
    round_type: str,
    difficulty: str,
    previous_questions: Optional[list] = None,
) -> str:
    if strategy not in PROMPT_STRATEGIES:
        raise ValueError(
            f"Unknown strategy '{strategy}'. "
            f"Available strategies: {', '.join(PROMPT_STRATEGIES.keys())}"
        )
    
    prompt_function = PROMPT_STRATEGIES[strategy]["function"]
    return prompt_function(role, company, round_type, difficulty, previous_questions)


def get_available_strategies() -> dict:
    return PROMPT_STRATEGIES
