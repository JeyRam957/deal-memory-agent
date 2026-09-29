import streamlit as st
import os

from dotenv import load_dotenv
from hindsight_client import Hindsight


load_dotenv()

BANK_ID = "deal-memory-agent"

hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)


st.set_page_config(
    page_title="DealMind - Memory Explorer",
    page_icon="🧠",
    layout="wide"
)


st.title("🧠 Memory Explorer")

st.caption(
    "Explore the long-term customer memory stored by DealMind."
)

st.divider()


company = st.selectbox(
    "Select Customer",
    [
        "TechNova Solutions",
        "GreenGrid Energy",
        "FinCore Bank"
    ]
)


query = st.text_input(
    "🔎 Search customer memory",
    value=f"Important information about {company}"
)


if st.button(
    "🧠 Recall Memories",
    type="primary",
    use_container_width=True
):

    with st.spinner("Searching DealMind memory..."):

        try:

            result = hindsight.recall(
                bank_id=BANK_ID,
                query=query
            )

            memories = result.results

            st.session_state["memories"] = memories

        except Exception as e:

            st.error(
                f"Memory search failed: {e}"
            )


if "memories" in st.session_state:

    memories = st.session_state["memories"]

    st.divider()

    st.subheader(
        f"🧠 Memories for {company}"
    )

    if not memories:

        st.info(
            "No relevant memories found."
        )

    else:

        st.success(
            f"Found {len(memories)} relevant memories."
        )

        for index, memory in enumerate(memories, 1):

            text = getattr(
                memory,
                "text",
                ""
            )

            if not text:
                continue

            with st.container(border=True):

                st.markdown(
                    f"### Memory {index}"
                )

                st.write(text)

                memory_type = getattr(
                    memory,
                    "type",
                    None
                )

                if memory_type:

                    st.caption(
                        f"Memory type: {memory_type}"
                    )