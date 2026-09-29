import streamlit as st
import os
from pathlib import Path


st.set_page_config(
    page_title="DealMind - Call Recordings",
    page_icon="📞",
    layout="wide"
)


st.title("📞 Call Recordings")

st.caption(
    "Review customer call recordings captured by DealMind."
)

st.divider()


RECORDING_DIR = Path("recordings")

if not RECORDING_DIR.exists():
    RECORDING_DIR.mkdir(parents=True)


recordings = sorted(
    RECORDING_DIR.glob("*.wav"),
    key=lambda x: x.stat().st_mtime,
    reverse=True
)


# -----------------------------
# METRICS
# -----------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "📞 Total Calls",
        len(recordings)
    )

with col2:
    st.metric(
        "🎙️ Audio Files",
        len(recordings)
    )

with col3:
    st.metric(
        "🧠 AI Platform",
        "DealMind"
    )


st.divider()


if not recordings:

    st.info(
        "No call recordings found yet. "
        "Record a customer conversation from Voice Assistant."
    )

else:

    st.subheader("Recent Customer Calls")

    for recording in recordings:

        file_size = recording.stat().st_size / 1024

        with st.container(border=True):

            col1, col2 = st.columns([4, 1])

            with col1:

                st.write(
                    f"📞 **{recording.name}**"
                )

                st.caption(
                    f"Audio size: {file_size:.1f} KB"
                )

                with open(recording, "rb") as audio_file:

                    st.audio(
                        audio_file.read(),
                        format="audio/wav"
                    )

            with col2:

                st.write("")

                if st.button(
                    "Delete",
                    key=f"delete_{recording.name}"
                ):

                    recording.unlink()

                    st.success(
                        "Recording deleted."
                    )

                    st.rerun()