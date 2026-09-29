import streamlit as st

from components.voice_ui import render_voice_assistant


st.set_page_config(
    page_title="DealMind - Voice Assistant",
    page_icon="🎙️",
    layout="wide"
)


st.title("🎙️ DealMind Voice Assistant")

st.caption(
    "Record a customer conversation and convert it into "
    "AI-powered deal intelligence."
)


company = st.selectbox(
    "Select Customer",
    [
        "TechNova Solutions",
        "GreenGrid Energy",
        "FinCore Bank"
    ]
)


st.divider()


render_voice_assistant(company)