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


def transcribe_audio(audio_bytes, filename="call.wav"):
    """
    Convert customer call audio into text using Groq Whisper.
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
    Analyze a customer conversation using Groq.
    """

    prompt = f"""
You are DealMind, an AI sales intelligence assistant.

Analyze the following customer conversation.

Company:
{company}

Customer conversation:
{transcript}

Return the analysis using exactly these sections:

CALL SUMMARY
Give a short summary.

CUSTOMER NEEDS
List the main customer requirements.

OBJECTIONS
List every customer objection or concern.

SENTIMENT
Describe the customer's overall conversation sentiment.

COMPETITORS
Mention competitors only if they appear in the conversation.

BUYING SIGNALS
Identify signs that the customer may be interested in moving forward.

RISKS
Identify risks that could slow down the deal.

NEXT ACTION
Give the most relevant next action for the salesperson.

IMPORTANT:
Use only information from the conversation.
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


def store_call_memory(company, transcript, analysis):
    """
    Store the call and AI analysis in Hindsight
    for future conversations.
    """

    memory = f"""
DealMind Customer Call Memory

Company:
{company}

Customer Call Transcript:
{transcript}

AI Call Analysis:
{analysis}
"""

    hindsight.retain(
        bank_id=BANK_ID,
        content=memory
    )

    return True


def process_call(company, audio_bytes):
    """
    Complete Phase 2 pipeline:

    Audio
       ↓
    Speech-to-text
       ↓
    AI analysis
       ↓
    Hindsight memory
    """

    transcript = transcribe_audio(audio_bytes)

    analysis = analyze_call(
        company,
        transcript
    )

    store_call_memory(
        company,
        transcript,
        analysis
    )

    return {
        "transcript": transcript,
        "analysis": analysis
    }