import os
import json

from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()

BANK_ID = "deal-memory-agent"

# Hindsight
hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

# Groq
groq = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def recall_memories(query):
    """Retrieve relevant memories from Hindsight."""
    result = hindsight.recall(
        bank_id=BANK_ID,
        query=query
    )

    return result.results


def create_pre_call_brief(company):
    """Create a sales pre-call brief using Hindsight memory + Groq."""

    memories = recall_memories(
        f"Give me all important information about {company}, "
        f"including contact, objections, competitors, deal stage, "
        f"previous discussions and next actions."
    )

    if not memories:
        return "No relevant memories found."

    memory_text = "\n".join(
        f"- {memory.text}"
        for memory in memories
    )

    prompt = f"""
You are an AI sales assistant.

Create a concise pre-call briefing for a sales representative.

Company:
{company}

Information retrieved from long-term memory:
{memory_text}

Create the briefing using these sections:

1. Contact
2. Deal Stage
3. Key Concerns
4. Competitor
5. Previous Discussion
6. Recommended Talking Points
7. Next Action

Use ONLY the information provided in the memory.
Do not invent facts.
"""

    response = groq.chat.completions.create(
        model=os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


if __name__ == "__main__":

    print("=" * 60)
    print("DEAL MEMORY AGENT")
    print("=" * 60)

    company = "TechNova Solutions"

    print(f"\nCreating pre-call brief for: {company}\n")

    brief = create_pre_call_brief(company)

    print(brief)