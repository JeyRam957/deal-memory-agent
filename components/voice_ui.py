import streamlit as st

from agent.ai_engine import process_call
from agent.analysis_parser import parse_analysis


def render_voice_assistant(company):

    st.title("🎙️ DealMind Voice Assistant")

    st.caption(
        "Record a customer conversation and convert it into "
        "AI-powered deal intelligence."
    )

    st.info(f"🏢 Customer: **{company}**")

    st.divider()

    # -----------------------------
    # RECORDING
    # -----------------------------

    consent = st.checkbox(
        "I confirm that recording consent has been obtained."
    )

    audio = st.audio_input(
        "🎙️ Record Customer Call"
    )

    if audio is not None:

        st.audio(
            audio,
            format="audio/wav"
        )

        st.success("Recording captured successfully.")

        if not consent:

            st.warning(
                "Please confirm recording consent before analysis."
            )

        else:

            if st.button(
                "🤖 Analyze Call with DealMind",
                type="primary",
                use_container_width=True
            ):

                with st.spinner(
                    "DealMind is transcribing and analyzing the call..."
                ):

                    try:

                        result = process_call(
                            company,
                            audio.getvalue()
                        )

                        st.session_state["call_result"] = result

                    except Exception as e:

                        st.error(
                            f"Call analysis failed: {e}"
                        )

    # -----------------------------
    # RESULTS
    # -----------------------------

    if "call_result" not in st.session_state:
        return

    result = st.session_state["call_result"]

    analysis = result["analysis"]

    parsed = parse_analysis(analysis)

    st.divider()

    st.header("🧠 DealMind Call Intelligence")

    # -----------------------------
    # RISK / SENTIMENT / MEMORY
    # -----------------------------

    risk = parsed.get("DEAL RISK", "").strip()
    sentiment = parsed.get("SENTIMENT", "").strip()

    col1, col2, col3 = st.columns(3)

    with col1:

        if "HIGH" in risk.upper():

            st.error(f"⚠️ Deal Risk\n\n{risk}")

        elif "MEDIUM" in risk.upper():

            st.warning(f"⚠️ Deal Risk\n\n{risk}")

        else:

            st.success(f"🟢 Deal Risk\n\n{risk or 'Unknown'}")

    with col2:

        st.metric(
            "💬 Sentiment",
            sentiment or "Unknown"
        )

    with col3:

        st.metric(
            "🧠 Memory",
            "Stored"
        )

    # -----------------------------
    # NEXT BEST ACTION
    # -----------------------------

    next_action = parsed.get(
        "NEXT BEST ACTION",
        ""
    ).strip()

    if next_action:

        st.subheader("🎯 Next Best Action")

        st.success(
            next_action
        )

    # -----------------------------
    # ISSUES
    # -----------------------------

    issues = parsed.get(
        "ISSUES DETECTED",
        ""
    ).strip()

    if issues:

        st.subheader("🚨 Issues Detected")

        st.warning(
            issues
        )

    # -----------------------------
    # CUSTOMER NEEDS
    # -----------------------------

    needs = parsed.get(
        "CUSTOMER NEEDS",
        ""
    ).strip()

    if needs:

        st.subheader("👤 Customer Needs")

        st.info(
            needs
        )

    # -----------------------------
    # OBJECTIONS
    # -----------------------------

    objections = parsed.get(
        "OBJECTIONS",
        ""
    ).strip()

    if objections:

        st.subheader("💬 Customer Objections")

        st.warning(
            objections
        )

    # -----------------------------
    # BUYING SIGNALS
    # -----------------------------

    signals = parsed.get(
        "BUYING SIGNALS",
        ""
    ).strip()

    if signals:

        st.subheader("🟢 Buying Signals")

        st.success(
            signals
        )

    # -----------------------------
    # RISK REASON
    # -----------------------------

    risk_reason = parsed.get(
        "RISK REASON",
        ""
    ).strip()

    if risk_reason:

        st.subheader("📊 Risk Reason")

        st.write(
            risk_reason
        )

    # -----------------------------
    # FOLLOW-UP QUESTIONS
    # -----------------------------

    questions = parsed.get(
        "FOLLOW-UP QUESTIONS",
        ""
    ).strip()

    if questions:

        st.subheader("❓ Follow-up Questions")

        st.info(
            questions
        )

    # -----------------------------
    # TRANSCRIPT
    # -----------------------------

    with st.expander(
        "📝 View Full Conversation Transcript"
    ):

        st.text_area(
            "Transcript",
            result["transcript"],
            height=220,
            disabled=True
        )

    # -----------------------------
    # FULL AI ANALYSIS
    # -----------------------------

    with st.expander(
        "🤖 View Full AI Analysis"
    ):

        st.markdown(
            analysis
        )

    st.success(
        "🧠 Call intelligence stored in Hindsight "
        "for future DealMind conversations."
    )