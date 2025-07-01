from pydantic import BaseModel
from providers import get_model
from prompt import system_prompt

class FeedbackResponse(BaseModel):
    questions: list[str]

def generate_feedback(query: str, num_questions: int = 3) -> list[str]:
    model = get_model()
    prompt = f"""Given the following user query, ask up to {num_questions} follow-up questions to clarify the research direction.

<query>{query}</query>
"""

    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": prompt},
    ]

    raw_output = model.generate(messages)
    questions = [
        q.strip("- ").strip()
        for q in raw_output.split("\n")
        if q.strip()
    ][:num_questions]

    return questions
