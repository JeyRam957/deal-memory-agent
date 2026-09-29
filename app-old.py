import os
import streamlit as st
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()

BANK_ID = "deal-memory-agent"

hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

groq = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def recall_memories(query):
    result = hindsight.recall(
        bank_id=BANK_ID,
        query=query
    )
    return result.results


def create_pre_call_brief(company):

    memories = recall_memories(
        f"""
        Give me important information about {company}.
        Include contact, role, deal stage, objections,
        competitor, previous discussions and next actions.
        """
    )

    if not memories:
        return "No relevant memories found."

    memory_text = "\n".join(
        f"- {memory.text}" for memory in memories
    )

    prompt = f"""
You are an AI sales assistant.

Create a concise pre-call briefing for:

Company: {company}

Long-term memory retrieved from Hindsight:
{memory_text}

Use these sections:

1. Contact
2. Deal Stage
3. Key Concerns
4. Competitor
5. Previous Discussion
6. Recommended Talking Points
7. Next Action

Use only information contained in the retrieved memory.
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


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="Deal Memory Agent",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Deal Memory Agent")
st.subheader("AI Sales Assistant powered by Hindsight")

st.markdown(
    """
This assistant remembers previous customer interactions
and uses those memories to prepare sales representatives
before their next call.
"""
)

st.divider()

company = st.selectbox(
    "Select a company",
    [
        "TechNova Solutions",
        "GreenGrid Energy",
        "FinCore Bank"
    ]
)

if st.button("Generate Pre-Call Brief", type="primary"):

    with st.spinner("Recalling memories and preparing briefing..."):

        brief = create_pre_call_brief(company)

    st.success("Pre-call briefing generated!")

    st.markdown("## 📋 Pre-Call Brief")

    st.markdown(brief)

st.divider()

st.caption(
    "Memory powered by Hindsight • LLM powered by Groq"
)