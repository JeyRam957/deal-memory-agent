import os
import json
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# Optional AI / Memory imports
try:
    from hindsight_client import Hindsight
except Exception:
    Hindsight = None

try:
    from groq import Groq
except Exception:
    Groq = None


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

APP_NAME = "DealMind"
BANK_ID = "deal-memory-agent"

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "deal_data.json"
RECORDINGS_DIR = BASE_DIR / "recordings"

RECORDINGS_DIR.mkdir(exist_ok=True)

HINDSIGHT_URL = os.getenv("HINDSIGHT_URL")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


# ============================================================
# CLIENTS
# ============================================================

@st.cache_resource
def get_hindsight():
    if not Hindsight:
        return None

    if not HINDSIGHT_URL or not HINDSIGHT_API_KEY:
        return None

    try:
        return Hindsight(
            base_url=HINDSIGHT_URL,
            api_key=HINDSIGHT_API_KEY
        )
    except Exception:
        return None


@st.cache_resource
def get_groq():
    if not Groq:
        return None

    if not GROQ_API_KEY:
        return None

    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception:
        return None


hindsight = get_hindsight()
groq = get_groq()


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_deals():
    if not DATA_FILE.exists():
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Could not load deal data: {e}")
        return []


deals = load_deals()


# ============================================================
# DATA HELPERS
# ============================================================

def get_companies():
    return [deal.get("company", "Unknown") for deal in deals]


def get_deal(company):
    for deal in deals:
        if deal.get("company") == company:
            return deal
    return None


def get_all_issues():
    issues = []

    for deal in deals:
        for issue in deal.get("issues", []):
            item = dict(issue)
            item["company"] = deal.get("company")
            item["deal_id"] = deal.get("deal_id")
            item["contact"] = deal.get("contact")
            issues.append(item)

    return issues


def get_active_issues(deal):
    return [
        issue
        for issue in deal.get("issues", [])
        if issue.get("status", "").lower() == "active"
    ]


def get_resolved_issues(deal):
    return [
        issue
        for issue in deal.get("issues", [])
        if issue.get("status", "").lower() == "resolved"
    ]


def average_resolution(deal):
    values = [
        issue.get("resolution_days")
        for issue in deal.get("issues", [])
        if issue.get("resolution_days") is not None
    ]

    if not values:
        return 0

    return round(sum(values) / len(values), 1)


def deal_health(deal):
    active = len(get_active_issues(deal))

    if active == 0:
        return "Healthy"

    if active <= 1:
        return "Watch"

    return "At Risk"


def health_icon(health):
    if health == "Healthy":
        return "🟢"

    if health == "Watch":
        return "🟡"

    return "🔴"


def get_conversations(deal):
    return deal.get("conversations", [])


# ============================================================
# HINDSIGHT
# ============================================================

def recall_memories(query):
    if not hindsight:
        return []

    try:
        result = hindsight.recall(
            bank_id=BANK_ID,
            query=query
        )

        return result.results or []

    except Exception as e:
        st.warning(f"Hindsight recall failed: {e}")
        return []


def store_memory(content):
    if not hindsight:
        return False

    try:
        hindsight.retain(
            bank_id=BANK_ID,
            content=content
        )
        return True

    except Exception as e:
        st.warning(f"Could not store memory: {e}")
        return False


# ============================================================
# GROQ
# ============================================================

def ask_groq(prompt):
    if not groq:
        return None

    try:
        response = groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are DealMind, an AI sales intelligence "
                        "assistant. Use only the information provided. "
                        "Do not invent customer facts."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Groq error: {e}")
        return None


def generate_pre_call_brief(company):
    memories = recall_memories(
        f"""
        Give me all important information about {company}.
        Include contact, objections, competitors, deal stage,
        previous discussions, customer concerns and next actions.
        """
    )

    memory_text = "\n".join(
        f"- {memory.text}"
        for memory in memories
        if getattr(memory, "text", None)
    )

    deal = get_deal(company)

    if not memory_text and deal:
        memory_text = json.dumps(deal, indent=2)

    prompt = f"""
Create a professional pre-call briefing.

Company:
{company}

Long-term customer memory:
{memory_text}

Create:

1. Customer
2. Deal Stage
3. Current Issues
4. Previous Discussions
5. Competitor
6. Customer Priorities
7. Recommended Talking Points
8. Next Best Action

Use only the supplied information.
Do not invent information.
"""

    return ask_groq(prompt)


# ============================================================
# VOICE PROCESSING
# ============================================================

def transcribe_audio(audio_bytes):
    if not groq:
        return None

    temp_file = RECORDINGS_DIR / "_temp_call.wav"

    try:
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)

        with open(temp_file, "rb") as audio_file:
            result = groq.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo"
            )

        return result.text

    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None

    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


def analyze_call(company, transcript):
    deal = get_deal(company)

    previous_context = ""

    if deal:
        previous_context = json.dumps(
            {
                "deal_stage": deal.get("deal_stage"),
                "competitor": deal.get("competitor"),
                "issues": deal.get("issues"),
                "next_action": deal.get("next_action")
            },
            indent=2
        )

    prompt = f"""
Analyze this customer sales call for DealMind.

Company:
{company}

Existing deal information:
{previous_context}

Call transcript:
{transcript}

Return a professional analysis with:

CALL SUMMARY
KEY CUSTOMER POINTS
NEW ISSUES
RESOLVED ISSUES
CUSTOMER SENTIMENT
COMPETITOR MENTIONS
BUYING SIGNALS
RISK SIGNALS
FOLLOW-UP ACTIONS
NEXT BEST ACTION

Do not invent facts.
"""

    return ask_groq(prompt)


# ============================================================
# GLOBAL CSS
# ============================================================

st.html(
    """
    <style>

    .deal-card {
        padding: 24px;
        border-radius: 18px;
        background: linear-gradient(
            135deg,
            #111827,
            #1e293b
        );
        color: white;
        margin-bottom: 25px;
    }

    .deal-label {
        color: #60a5fa;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 1px;
    }

    .deal-title {
        font-size: 36px;
        font-weight: 800;
        margin-top: 8px;
    }

    .deal-subtitle {
        color: #dbeafe;
        font-size: 17px;
    }

    .status-pill {
        display: inline-block;
        margin-top: 18px;
        padding: 8px 14px;
        border-radius: 20px;
        background: #334155;
        color: white;
    }

    .section-card {
        padding: 20px;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        margin-bottom: 15px;
    }

    .issue-active {
        border-left: 5px solid #ef4444;
    }

    .issue-resolved {
        border-left: 5px solid #22c55e;
    }

    .small-muted {
        color: #64748b;
        font-size: 13px;
    }

    </style>
    """
)


# ============================================================
# SIDEBAR BRAND
# ============================================================

st.sidebar.markdown(
    """
    # 🧠 DEALMIND
    ### AI Deal Intelligence
    """
)

st.sidebar.caption(
    "Persistent customer memory • AI sales intelligence"
)

st.sidebar.divider()


# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():

    st.title("DealMind Dashboard")

    st.caption(
        "Persistent customer memory, issue intelligence and sales activity."
    )

    if not deals:
        st.error(
            "No deal data found. Check data/deal_data.json."
        )
        return

    company = st.selectbox(
        "Customer",
        get_companies(),
        key="dashboard_customer"
    )

    deal = get_deal(company)

    if not deal:
        st.error("Customer not found.")
        return

    active = get_active_issues(deal)
    resolved = get_resolved_issues(deal)
    total = len(deal.get("issues", []))
    conversations = get_conversations(deal)

    health = deal_health(deal)

    # Hero
    st.html(
        f"""
        <div class="deal-card">
            <div class="deal-label">
                DEALMIND • CUSTOMER INTELLIGENCE
            </div>

            <div class="deal-title">
                {deal.get("company")}
            </div>

            <div class="deal-subtitle">
                {deal.get("contact")} •
                {deal.get("role")} •
                {deal.get("industry")}
            </div>

            <div class="status-pill">
                Deal Stage: {deal.get("deal_stage")}
                &nbsp; • &nbsp;
                {health_icon(health)} Health: {health}
            </div>
        </div>
        """
    )

    # Metrics
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Active Issues",
            len(active)
        )

    with c2:
        st.metric(
            "Resolved Issues",
            len(resolved)
        )

    with c3:
        st.metric(
            "Total Issues",
            total
        )

    with c4:
        st.metric(
            "Conversations",
            len(conversations)
        )

    st.divider()

    # Next action
    st.subheader("🎯 Recommended Next Action")

    st.info(
        deal.get(
            "next_action",
            "No next action available."
        )
    )

    # Customer snapshot
    st.subheader("👤 Customer Snapshot")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.write("**Contact**")
        st.write(deal.get("contact"))

        st.write("**Role**")
        st.write(deal.get("role"))

    with c2:
        st.write("**Industry**")
        st.write(deal.get("industry"))

        st.write("**Deal Stage**")
        st.write(deal.get("deal_stage"))

    with c3:
        st.write("**Competitor**")
        st.write(deal.get("competitor"))

        st.write("**Avg Resolution**")
        st.write(f"{average_resolution(deal)} days")

    st.divider()

    # Active issues
    st.subheader("⚠️ Active Issues")

    if active:

        for issue in active:

            with st.container(border=True):

                c1, c2 = st.columns([3, 1])

                with c1:
                    st.markdown(
                        f"### 🔴 {issue.get('title')}"
                    )

                    st.caption(
                        f"Opened: {issue.get('opened_date')}"
                    )

                with c2:
                    st.error("ACTIVE")

    else:
        st.success("No active customer issues.")

    # Recent conversations
    st.subheader("💬 Recent Customer Conversations")

    for conversation in reversed(conversations[-3:]):

        with st.container(border=True):

            st.markdown(
                f"**{conversation.get('date')}**"
            )

            st.write(
                conversation.get("summary")
            )

            st.caption(
                "Customer: "
                + conversation.get(
                    "customer_statement",
                    ""
                )
            )


# ============================================================
# ISSUES PAGE
# ============================================================

def issues_page():

    st.title("⚠️ Issue Intelligence")

    st.caption(
        "Track customer problems from opening to resolution."
    )

    all_issues = get_all_issues()

    if not all_issues:
        st.info("No issues available.")
        return

    status = st.selectbox(
        "Filter",
        ["All", "Active", "Resolved"]
    )

    filtered = all_issues

    if status != "All":
        filtered = [
            issue
            for issue in all_issues
            if issue.get("status") == status
        ]

    st.metric(
        "Issues shown",
        len(filtered)
    )

    st.divider()

    for issue in filtered:

        active = issue.get("status") == "Active"

        with st.container(border=True):

            if active:
                st.markdown(
                    f"### 🔴 {issue.get('title')}"
                )
            else:
                st.markdown(
                    f"### 🟢 {issue.get('title')}"
                )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.write(
                    f"**Customer:** {issue.get('company')}"
                )

            with c2:
                st.write(
                    f"**Status:** {issue.get('status')}"
                )

            with c3:
                days = issue.get("resolution_days")

                if days:
                    st.write(
                        f"**Resolution:** {days} days"
                    )
                else:
                    st.write(
                        "**Resolution:** Open"
                    )

            st.caption(
                f"Opened: {issue.get('opened_date')}"
            )

            if issue.get("resolved_date"):
                st.caption(
                    f"Resolved: {issue.get('resolved_date')}"
                )

            if issue.get("resolution_note"):
                st.write(
                    issue.get("resolution_note")
                )


# ============================================================
# ANALYTICS PAGE
# ============================================================

def analytics_page():

    st.title("📊 Deal Analytics")

    st.caption(
        "Understand issue volume, resolution performance and deal health."
    )

    if not deals:
        return

    # Overall metrics
    all_issues = get_all_issues()

    active_count = sum(
        1 for x in all_issues
        if x.get("status") == "Active"
    )

    resolved_count = sum(
        1 for x in all_issues
        if x.get("status") == "Resolved"
    )

    resolution_values = [
        x.get("resolution_days")
        for x in all_issues
        if x.get("resolution_days") is not None
    ]

    avg_resolution = (
        round(
            sum(resolution_values)
            / len(resolution_values),
            1
        )
        if resolution_values
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Total Deals",
            len(deals)
        )

    with c2:
        st.metric(
            "Active Issues",
            active_count
        )

    with c3:
        st.metric(
            "Resolved Issues",
            resolved_count
        )

    with c4:
        st.metric(
            "Avg Resolution",
            f"{avg_resolution} days"
        )

    st.divider()

    # Issue distribution
    st.subheader("Issue Distribution")

    issue_data = {
        "Active": active_count,
        "Resolved": resolved_count
    }

    st.bar_chart(issue_data)

    st.divider()

    # Deal overview
    st.subheader("Deal Overview")

    for deal in deals:

        active = len(get_active_issues(deal))
        resolved = len(get_resolved_issues(deal))

        st.write(
            f"**{deal.get('company')}**"
        )

        st.progress(
            resolved / max(
                active + resolved,
                1
            )
        )

        st.caption(
            f"{resolved} resolved • "
            f"{active} active"
        )


# ============================================================
# TIMELINE PAGE
# ============================================================

def timeline_page():

    st.title("🕒 Conversation Timeline")

    st.caption(
        "Historical customer conversations stored in DealMind."
    )

    if not deals:
        return

    company = st.selectbox(
        "Customer",
        get_companies(),
        key="timeline_customer"
    )

    deal = get_deal(company)

    conversations = deal.get(
        "conversations",
        []
    )

    if not conversations:
        st.info("No conversations.")
        return

    for conversation in conversations:

        with st.container(border=True):

            st.markdown(
                f"### 📅 {conversation.get('date')}"
            )

            st.write(
                conversation.get("summary")
            )

            st.info(
                conversation.get(
                    "customer_statement",
                    ""
                )
            )

            objections = conversation.get(
                "objections",
                []
            )

            if objections:
                st.caption(
                    "Issues discussed: "
                    + ", ".join(objections)
                )


# ============================================================
# AI INTELLIGENCE PAGE
# ============================================================

def ai_intelligence_page():

    st.title("🤖 AI Intelligence")

    st.caption(
        "Generate an AI-powered customer briefing using long-term memory."
    )

    if not deals:
        return

    company = st.selectbox(
        "Customer",
        get_companies(),
        key="ai_customer"
    )

    deal = get_deal(company)

    c1, c2 = st.columns(2)

    with c1:
        st.write("**Contact**")
        st.write(
            f"{deal.get('contact')} • {deal.get('role')}"
        )

    with c2:
        st.write("**Deal**")
        st.write(
            f"{deal.get('deal_stage')} • "
            f"{deal.get('competitor')}"
        )

    st.divider()

    if st.button(
        "🧠 Generate AI Pre-Call Brief",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Recalling customer memory and generating intelligence..."
        ):

            result = generate_pre_call_brief(
                company
            )

        if result:
            st.markdown(result)

        else:
            st.warning(
                "AI response unavailable. "
                "Check your GROQ_API_KEY and HINDSIGHT settings."
            )


# ============================================================
# VOICE ASSISTANT PAGE
# ============================================================

def voice_page():

    st.title("🎙️ Voice Assistant")

    st.caption(
        "Record a customer call, transcribe it and generate AI intelligence."
    )

    if not deals:
        return

    company = st.selectbox(
        "Customer",
        get_companies(),
        key="voice_customer"
    )

    st.info(
        "Record a short customer conversation. "
        "DealMind will save the recording, transcribe it "
        "and analyze the conversation."
    )

    consent = st.checkbox(
        "I confirm that recording consent has been obtained."
    )

    audio = st.audio_input(
        "🎙️ Record customer conversation",
        sample_rate=16000
    )

    if audio:

        st.audio(
            audio
        )

        st.write(
            f"Recording size: "
            f"{len(audio.getvalue()) / 1024:.1f} KB"
        )

        if not consent:
            st.warning(
                "Please confirm recording consent before processing."
            )

        if consent:

            if st.button(
                "🧠 Analyze Customer Call",
                type="primary",
                use_container_width=True
            ):

                audio_bytes = audio.getvalue()

                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                filename = (
                    f"customer_call_"
                    f"{timestamp}.wav"
                )

                filepath = (
                    RECORDINGS_DIR / filename
                )

                # Save recording
                with open(filepath, "wb") as f:
                    f.write(audio_bytes)

                st.success(
                    f"Recording saved: {filename}"
                )

                # Transcription
                with st.spinner(
                    "Transcribing customer call..."
                ):

                    transcript = transcribe_audio(
                        audio_bytes
                    )

                if transcript:

                    st.subheader(
                        "📝 Call Transcript"
                    )

                    st.write(transcript)

                    # AI analysis
                    with st.spinner(
                        "Analyzing customer conversation..."
                    ):

                        analysis = analyze_call(
                            company,
                            transcript
                        )

                    if analysis:

                        st.subheader(
                            "🤖 AI Call Intelligence"
                        )

                        st.markdown(
                            analysis
                        )

                    # Store in Hindsight
                    memory = f"""
DealMind Customer Call Memory

Company:
{company}

Call Date:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Transcript:
{transcript}

AI Analysis:
{analysis or "No AI analysis available."}
"""

                    if store_memory(memory):

                        st.success(
                            "✅ Call intelligence stored in Hindsight memory."
                        )


# ============================================================
# CALL RECORDINGS PAGE
# ============================================================

def recordings_page():

    st.title("📞 Call Recordings")

    st.caption(
        "Stored customer conversation recordings."
    )

    recordings = sorted(
        RECORDINGS_DIR.glob("*.wav"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not recordings:
        st.info(
            "No recordings yet. "
            "Use Voice Assistant to create one."
        )
        return

    st.write(
        f"**{len(recordings)} recording(s)**"
    )

    for recording in recordings:

        with st.container(border=True):

            st.markdown(
                f"### 🎙️ {recording.name}"
            )

            size_kb = (
                recording.stat().st_size / 1024
            )

            st.caption(
                f"{size_kb:.1f} KB"
            )

            with open(recording, "rb") as f:
                audio_bytes = f.read()

            st.audio(
                audio_bytes,
                format="audio/wav"
            )


# ============================================================
# MEMORY EXPLORER PAGE
# ============================================================

def memory_explorer_page():

    st.title("🧠 Memory Explorer")

    st.caption(
        "Explore the long-term customer memory stored by DealMind."
    )

    if not deals:
        return

    company = st.selectbox(
        "Select Customer",
        get_companies(),
        key="memory_customer"
    )

    default_query = (
        f"Important information about {company}"
    )

    query = st.text_input(
        "🔎 Search customer memory",
        value=default_query
    )

    if st.button(
        "🧠 Recall Memories",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Searching Hindsight long-term memory..."
        ):

            memories = recall_memories(
                query
            )

        if not memories:

            st.warning(
                "No memories found."
            )

        else:

            st.success(
                f"Found {len(memories)} memory result(s)."
            )

            for index, memory in enumerate(
                memories,
                start=1
            ):

                text_value = getattr(
                    memory,
                    "text",
                    ""
                )

                if not text_value:
                    continue

                memory_type = getattr(
                    memory,
                    "type",
                    "Memory"
                )

                with st.container(border=True):

                    st.markdown(
                        f"### 🧠 Memory {index}"
                    )

                    st.caption(
                        f"Type: {memory_type}"
                    )

                    st.write(
                        text_value
                    )


# ============================================================
# SYSTEM STATUS PAGE
# ============================================================

def system_status_page():

    st.title("⚙️ System Status")

    st.caption(
        "Check DealMind services."
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if hindsight:
            st.success("Hindsight Connected")
        else:
            st.error("Hindsight Not Connected")

    with c2:

        if groq:
            st.success("Groq Connected")
        else:
            st.error("Groq Not Connected")

    with c3:

        if RECORDINGS_DIR.exists():
            st.success("Recording Storage Ready")
        else:
            st.error("Recording Storage Error")

    st.divider()

    st.subheader("Configuration")

    st.write(
        f"**Memory Bank:** `{BANK_ID}`"
    )

    st.write(
        f"**AI Model:** `{GROQ_MODEL}`"
    )

    st.write(
        f"**Recordings:** `{RECORDINGS_DIR}`"
    )

    st.write(
        f"**Deals Loaded:** `{len(deals)}`"
    )


# ============================================================
# NAVIGATION
# ============================================================

dashboard = st.Page(
    dashboard_page,
    title="Dashboard",
    icon=":material/dashboard:",
    default=True
)

issues = st.Page(
    issues_page,
    title="Issues",
    icon=":material/error:"
)

analytics = st.Page(
    analytics_page,
    title="Analytics",
    icon=":material/analytics:"
)

timeline = st.Page(
    timeline_page,
    title="Timeline",
    icon=":material/history:"
)

ai_intelligence = st.Page(
    ai_intelligence_page,
    title="AI Intelligence",
    icon=":material/psychology:"
)

voice = st.Page(
    voice_page,
    title="Voice Assistant",
    icon=":material/mic:"
)

recordings = st.Page(
    recordings_page,
    title="Call Recordings",
    icon=":material/audio_file:"
)

memory_explorer = st.Page(
    memory_explorer_page,
    title="Memory Explorer",
    icon=":material/psychology:"
)

system_status = st.Page(
    system_status_page,
    title="System Status",
    icon=":material/settings:"
)


# ============================================================
# STREAMLIT NAVIGATION
# ============================================================

pg = st.navigation(
    {
        "WORKSPACE": [
            dashboard,
            issues,
            analytics,
            timeline,
        ],

        "AI TOOLS": [
            ai_intelligence,
            memory_explorer,
        ],

        "VOICE": [
            voice,
            recordings,
        ],

        "SYSTEM": [
            system_status,
        ],
    },
    position="sidebar"
)

pg.run()