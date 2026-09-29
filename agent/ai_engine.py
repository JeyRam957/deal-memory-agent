import os
import tempfile

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight


load_dotenv()


BANK_ID = "deal-memory-agent"


groq = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)


def transcribe_audio(audio_bytes):
    """
    Convert recorded customer audio into text
    using Groq Whisper.
    """

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp_file:

            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        with open(temp_path, "rb") as audio_file:

            transcription = groq.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                response_format="text"
            )

        return transcription

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def analyze_call(company, transcript):
    """
    Analyze customer conversation and extract
    structured deal intelligence.
    """

    prompt = f"""
You are DealMind, an advanced AI sales intelligence system.

Analyze this customer conversation.

Company:
{company}

Conversation:
{transcript}

Return the following sections exactly:

CALL SUMMARY

CUSTOMER NEEDS

OBJECTIONS

ISSUES DETECTED

BUYING SIGNALS

SENTIMENT

DEAL RISK

RISK REASON

COMPETITORS

NEXT BEST ACTION

FOLLOW-UP QUESTIONS

Rules:

1. Use ONLY information contained in the conversation.
2. Do not invent customer information.
3. Do not assume competitors that were not mentioned.
4. For SENTIMENT choose:
   Positive
   Neutral
   Negative
   Mixed

5. For DEAL RISK choose:
   LOW
   MEDIUM
   HIGH

6. Give one clear NEXT BEST ACTION.
7. Give 2-3 useful FOLLOW-UP QUESTIONS.
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


def store_call_memory(company, transcript, analysis):
    """
    Store customer call information in Hindsight
    for future recall.
    """

    memory = f"""
DealMind Customer Call Memory

Company:
{company}

Customer Call Transcript:
{transcript}

AI Deal Intelligence:
{analysis}
"""

    hindsight.retain(
        bank_id=BANK_ID,
        content=memory
    )

    return True


def process_call(company, audio_bytes):
    """
    Complete DealMind call intelligence pipeline.

    Audio
       ↓
    Speech-to-text
       ↓
    AI analysis
       ↓
    Hindsight memory
    """

    # 1. Transcribe
    transcript = transcribe_audio(
        audio_bytes
    )

    # 2. Analyze
    analysis = analyze_call(
        company,
        transcript
    )

    # 3. Store in Hindsight
    store_call_memory(
        company,
        transcript,
        analysis
    )

    # 4. Return results to UI
    return {
        "transcript": transcript,
        "analysis": analysis
    }