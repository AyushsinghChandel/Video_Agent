"""
Video Agent — Streamlit front-end
Run with:  streamlit run app.py
"""
import html
import os
import re
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import streamlit as st
from dotenv import load_dotenv

# Must run before any core.* import (transcriber reads WHISPER_MODEL at import time)
load_dotenv()

st.set_page_config(
    page_title="Video Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

UPLOAD_TYPES = ["mp3", "wav", "m4a", "aac", "flac", "ogg", "mp4", "mov", "mkv", "webm"]

STAGES = [
    "Preparing audio",
    "Transcribing speech",
    "Crafting a title",
    "Writing the summary",
    "Extracting action items",
    "Finding key decisions",
    "Collecting open questions",
    "Indexing for chat",
]

SUGGESTIONS = [
    "What are the key takeaways?",
    "Who is speaking and what is the main topic?",
    "Were any deadlines or numbers mentioned?",
]

# ─────────────────────────────────────────────────────────────────────────────
# Styling
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root{
  --bg:#070A13; --bg2:#0D1220;
  --card:rgba(255,255,255,.045); --card-hi:rgba(255,255,255,.07);
  --stroke:rgba(255,255,255,.09);
  --txt:#E7EAF3; --muted:#8B93A7;
  --a1:#8B5CF6; --a2:#22D3EE; --a3:#F472B6;
}

html, body, .stApp, [class*="css"]{ font-family:'Inter',system-ui,sans-serif; }
.stApp{
  color:var(--txt);
  background:
    radial-gradient(1100px 560px at 8% -10%, rgba(139,92,246,.20), transparent 60%),
    radial-gradient(900px 500px at 100% 0%, rgba(34,211,238,.13), transparent 60%),
    radial-gradient(700px 500px at 50% 120%, rgba(244,114,182,.10), transparent 60%),
    var(--bg);
}
header[data-testid="stHeader"]{ background:transparent; }
[data-testid="stDecoration"], #MainMenu, footer{ display:none !important; }
.block-container{ padding-top:2.2rem; padding-bottom:4rem; max-width:1180px; }

h1,h2,h3,h4{ font-family:'Space Grotesk','Inter',sans-serif; letter-spacing:-.01em; }

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0B1020 0%,#080B16 100%);
  border-right:1px solid var(--stroke);
}
section[data-testid="stSidebar"] .stButton>button,
section[data-testid="stSidebar"] .stDownloadButton>button,
section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"]>button,
section[data-testid="stSidebar"] .stFormSubmitButton>button{ width:100%; }
/* hide Streamlit's "Press Enter to apply / submit" hint that overlaps the text */
[data-testid="InputInstructions"]{ display:none !important; }
[data-testid="stForm"]{ border:0 !important; padding:0 !important; background:transparent !important; }
.brand{ display:flex; align-items:center; gap:.8rem; margin:.2rem 0 1.4rem; }
.brand .logo{
  width:42px; height:42px; border-radius:12px; display:grid; place-items:center; font-size:1.3rem;
  background:linear-gradient(135deg,var(--a1),var(--a2));
  box-shadow:0 8px 28px rgba(139,92,246,.45);
}
.brand-name{ font-family:'Space Grotesk'; font-weight:700; font-size:1.2rem; color:#fff; line-height:1.1; }
.brand-sub{ color:var(--muted); font-size:.78rem; }
.sec-label{
  margin:1.3rem 0 .4rem; font-size:.7rem; font-weight:600; letter-spacing:.14em;
  text-transform:uppercase; color:var(--muted);
}
.side-feats{ display:flex; flex-direction:column; gap:.5rem; }
.sf{
  display:flex; align-items:center; gap:.7rem; padding:.55rem .7rem; border-radius:12px;
  background:var(--card); border:1px solid var(--stroke); transition:all .2s ease;
}
.sf:hover{ border-color:rgba(139,92,246,.5); background:var(--card-hi); transform:translateX(3px); }
.sf > span{ font-size:1.1rem; width:30px; height:30px; display:grid; place-items:center; border-radius:9px;
  background:linear-gradient(135deg,rgba(139,92,246,.28),rgba(34,211,238,.18)); }
.sf b{ display:block; color:#fff; font-size:.85rem; font-weight:600; }
.sf small{ display:block; color:var(--muted); font-size:.72rem; line-height:1.3; }
.tip{
  margin-top:1rem; padding:.7rem .85rem; border-radius:12px; font-size:.76rem; line-height:1.5; color:#B6BDD0;
  background:rgba(34,211,238,.06); border:1px solid rgba(34,211,238,.2);
}

/* ── Hero ────────────────────────────────────────────────── */
.hero{
  position:relative; overflow:hidden; border-radius:26px; padding:2.8rem 2.8rem 2.5rem;
  border:1px solid var(--stroke);
  background:linear-gradient(135deg,rgba(139,92,246,.17),rgba(34,211,238,.07) 55%,rgba(244,114,182,.09));
}
.hero::before, .hero::after{
  content:""; position:absolute; border-radius:50%; filter:blur(70px); opacity:.55; pointer-events:none;
}
.hero::before{ width:320px; height:320px; right:-80px; top:-120px; background:var(--a1); animation:float 9s ease-in-out infinite; }
.hero::after{ width:260px; height:260px; left:35%; bottom:-170px; background:var(--a2); animation:float 11s ease-in-out infinite reverse; }
@keyframes float{ 0%,100%{ transform:translateY(0) } 50%{ transform:translateY(26px) } }
.hero > *{ position:relative; z-index:1; }
.eyebrow{
  display:inline-flex; align-items:center; gap:.5rem; font-size:.74rem; font-weight:600; letter-spacing:.12em;
  text-transform:uppercase; color:#C4B5FD; background:rgba(139,92,246,.14);
  border:1px solid rgba(139,92,246,.35); padding:.3rem .8rem; border-radius:999px;
}
.hero h1{
  font-size:3.2rem; line-height:1.05; margin:1rem 0 .8rem; font-weight:700;
  background:linear-gradient(90deg,#fff 0%,#C4B5FD 45%,#67E8F9 100%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
.hero p{ color:#AEB6CA; font-size:1.05rem; max-width:620px; line-height:1.6; margin:0 0 1.4rem; }
.pills{ display:flex; flex-wrap:wrap; gap:.5rem; }
.pill{
  font-size:.78rem; color:#CBD5E1; padding:.3rem .75rem; border-radius:999px;
  background:rgba(255,255,255,.06); border:1px solid var(--stroke);
}

.feature-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:1.2rem; }
.feature{
  padding:1.4rem; border-radius:20px; background:var(--card); border:1px solid var(--stroke);
  transition:transform .25s ease, border-color .25s ease, background .25s ease;
}
.feature:hover{ transform:translateY(-4px); border-color:rgba(139,92,246,.5); background:var(--card-hi); }
.feature .ic{
  width:44px; height:44px; border-radius:12px; display:grid; place-items:center; font-size:1.3rem; margin-bottom:.9rem;
  background:linear-gradient(135deg,rgba(139,92,246,.30),rgba(34,211,238,.20)); border:1px solid var(--stroke);
}
.feature h4{ margin:0 0 .35rem; color:#fff; font-size:1.05rem; }
.feature p{ margin:0; color:var(--muted); font-size:.9rem; line-height:1.55; }
@media (max-width:900px){ .feature-grid{ grid-template-columns:1fr } .hero h1{ font-size:2.3rem } }

/* ── Result header + stat cards ──────────────────────────── */
.result-head .kicker{
  font-size:.72rem; font-weight:600; letter-spacing:.16em; color:var(--a2); text-transform:uppercase;
}
.result-head h2{
  margin:.35rem 0 .3rem; font-size:2.1rem; line-height:1.15; color:#fff; font-weight:700;
}
.result-head .src{ color:var(--muted); font-size:.85rem; word-break:break-all; }
.stat{
  padding:1.1rem 1.2rem; border-radius:18px; background:var(--card); border:1px solid var(--stroke);
  position:relative; overflow:hidden;
}
.stat::after{
  content:""; position:absolute; left:0; top:0; height:3px; width:100%;
  background:linear-gradient(90deg,var(--a1),var(--a2)); opacity:.8;
}
.stat .v{ font-family:'Space Grotesk'; font-size:1.9rem; font-weight:700; color:#fff; line-height:1.1; }
.stat .l{ margin-top:.25rem; color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.1em; }

/* ── Cards (st.container(key="card_*")) ──────────────────── */
[class*="st-key-card"]{
  background:var(--card); border:1px solid var(--stroke); border-radius:20px;
  padding:1.5rem 1.7rem; backdrop-filter:blur(10px);
}
[class*="st-key-card"] p, [class*="st-key-card"] li{ line-height:1.7; color:#D6DBE8; }
[class*="st-key-card"] strong{ color:#fff; }
[class*="st-key-card"] h1, [class*="st-key-card"] h2, [class*="st-key-card"] h3{ color:#fff; }

/* ── Tabs ────────────────────────────────────────────────── */
div[data-baseweb="tab-list"]{ gap:.3rem; border-bottom:1px solid var(--stroke); }
button[data-baseweb="tab"]{
  background:transparent; color:var(--muted); font-weight:600; padding:.7rem 1.1rem; border-radius:10px 10px 0 0;
}
button[data-baseweb="tab"]:hover{ color:#fff; background:rgba(255,255,255,.04); }
button[data-baseweb="tab"][aria-selected="true"]{ color:#fff; }
div[data-baseweb="tab-highlight"]{ background:linear-gradient(90deg,var(--a1),var(--a2)); height:3px; border-radius:3px; }
div[data-baseweb="tab-border"]{ display:none; }

/* ── Buttons ─────────────────────────────────────────────── */
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button, .stFormSubmitButton>button{
  border-radius:12px; border:1px solid var(--stroke); background:var(--card); color:var(--txt);
  font-weight:600; padding:.55rem 1rem; transition:all .2s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover{
  border-color:rgba(139,92,246,.6); color:#fff; background:rgba(139,92,246,.12); transform:translateY(-1px);
}
button[kind^="primary"], button[data-testid^="stBaseButton-primary"]{
  border:0; color:#fff; background:linear-gradient(90deg,var(--a1),#6D8BF5 50%,var(--a2));
  box-shadow:0 10px 32px rgba(139,92,246,.40); padding:.7rem 1rem; font-size:1rem;
}
button[kind^="primary"]:hover, button[data-testid^="stBaseButton-primary"]:hover{
  filter:brightness(1.12); box-shadow:0 14px 40px rgba(34,211,238,.35); transform:translateY(-2px);
}

/* ── Inputs ──────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea{
  background:rgba(255,255,255,.05) !important; border:1px solid var(--stroke) !important;
  border-radius:12px !important; color:#fff !important;
}
.stTextInput input:focus, .stTextArea textarea:focus{
  border-color:var(--a1) !important; box-shadow:0 0 0 3px rgba(139,92,246,.25) !important;
}
div[data-baseweb="select"]>div{
  background:rgba(255,255,255,.05) !important; border:1px solid var(--stroke) !important; border-radius:12px !important;
}
section[data-testid="stFileUploaderDropzone"], [data-testid="stFileUploaderDropzone"]{
  background:rgba(139,92,246,.06); border:1.5px dashed rgba(139,92,246,.55); border-radius:14px;
}
.stTextArea textarea{ font-size:.92rem; line-height:1.65; }

/* ── Status / progress ───────────────────────────────────── */
details, [data-testid="stStatusWidget"], [data-testid="stExpander"]{
  border:1px solid var(--stroke) !important; border-radius:16px !important; background:var(--card) !important;
}
.stProgress > div > div > div > div{ background:linear-gradient(90deg,var(--a1),var(--a2)); }

/* ── Chat ────────────────────────────────────────────────── */
div[data-testid="stChatMessage"]{
  background:rgba(255,255,255,.04); border:1px solid var(--stroke); border-radius:16px; padding:.9rem 1.1rem;
}
div[data-testid="stChatInput"]{ border-radius:16px; border:1px solid var(--stroke); background:var(--bg2); }
div[data-testid="stChatInput"]:focus-within{ border-color:var(--a1); box-shadow:0 0 0 3px rgba(139,92,246,.25); }
.chat-hint{ color:var(--muted); font-size:.82rem; margin-bottom:.8rem; }

::-webkit-scrollbar{ width:10px; height:10px; }
::-webkit-scrollbar-thumb{ background:rgba(255,255,255,.12); border-radius:10px; }
::-webkit-scrollbar-thumb:hover{ background:rgba(139,92,246,.5); }
</style>
"""

HERO_HTML = """
<div class="hero">
  <span class="eyebrow">● AI Video Assistant</span>
  <h1>Turn any video into<br>answers, not hours.</h1>
  <p>Drop a YouTube link or upload a recording. Video Agent transcribes it, writes the summary,
     pulls out action items and decisions, and lets you chat with everything that was said.</p>
  <div class="pills">
    <span class="pill">Whisper</span><span class="pill">Groq LLM</span>
    <span class="pill">LangChain</span><span class="pill">ChromaDB</span><span class="pill">RAG chat</span>
  </div>
</div>
<div class="feature-grid">
  <div class="feature"><div class="ic">🎙️</div><h4>Transcribe</h4>
    <p>Local Whisper turns speech into text, with optional translation to English.</p></div>
  <div class="feature"><div class="ic">🧠</div><h4>Understand</h4>
    <p>Get a title, summary, action items, key decisions and open questions in seconds.</p></div>
  <div class="feature"><div class="ic">💬</div><h4>Chat</h4>
    <p>Ask follow-up questions. Answers come only from what was actually said.</p></div>
</div>
"""

SIDEBAR_FEATURES_HTML = """
<div class="sec-label">What you get</div>
<div class="side-feats">
  <div class="sf"><span>📌</span><div><b>Smart title</b><small>A catchy headline for the video</small></div></div>
  <div class="sf"><span>📋</span><div><b>Bullet summary</b><small>Key points, no fluff</small></div></div>
  <div class="sf"><span>✅</span><div><b>Action items</b><small>Tasks, owners and deadlines</small></div></div>
  <div class="sf"><span>🔑</span><div><b>Key decisions</b><small>What was actually agreed</small></div></div>
  <div class="sf"><span>💬</span><div><b>Chat with video</b><small>Ask questions, get grounded answers</small></div></div>
</div>
<div class="tip">💡 Longer videos take longer — a 10 min video is split into chunks and processed step by step.</div>
"""

BRAND_HTML = """
<div class="brand">
  <div class="logo">🎬</div>
  <div><div class="brand-name">Video Agent</div><div class="brand-sub">AI video assistant</div></div>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Backend wiring
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading AI engines…")
def load_backend() -> SimpleNamespace:
    """Import the heavy modules once per server process."""
    from utils.audio_processor import process_input
    from core import transcriber
    from core.summarize import summarize, generate_title
    from core.extractor import extract_action_items, extract_key_decisions, extract_questions
    from core.rag_engine import build_rag_chain, ask_question

    return SimpleNamespace(
        process_input=process_input,
        transcriber=transcriber,
        summarize=summarize,
        generate_title=generate_title,
        extract_action_items=extract_action_items,
        extract_key_decisions=extract_key_decisions,
        extract_questions=extract_questions,
        build_rag_chain=build_rag_chain,
        ask_question=ask_question,
    )


def clean_title(raw: str) -> str:
    line = next((l for l in raw.splitlines() if l.strip()), "Untitled video")
    line = line.strip(" \"'*#_`")
    line = re.sub(r"^title\s*[:\-]\s*", "", line, flags=re.I)
    return line.strip(" \"'*#_`") or "Untitled video"


def save_upload(upload) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", upload.name)
    path = DOWNLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{safe}"
    path.write_bytes(upload.getbuffer())
    return str(path)


def analyze(source: str, label: str) -> dict:
    be = load_backend()

    started = time.time()
    total = len(STAGES)
    bar = st.progress(0.0, text="Starting…")

    def step(i: int):
        bar.progress(i / total, text=f"{STAGES[i]}…")

    with st.status("Analyzing your video…", expanded=True) as status:
        try:
            step(0)
            chunks = be.process_input(source)
            st.write(f"✅ Audio ready — {len(chunks)} chunk(s)")

            step(1)
            transcript = be.transcriber.transcribe_all(chunks)
            for c in chunks:  # tidy temporary chunk files
                try:
                    os.remove(c)
                except OSError:
                    pass
            if not transcript.strip():
                raise ValueError("No speech was detected in this audio.")
            st.write(f"✅ Transcribed {len(transcript.split()):,} words")

            step(2)
            title = clean_title(be.generate_title(transcript))
            st.write("✅ Title created")

            step(3)
            summary = be.summarize(transcript)
            st.write("✅ Summary written")

            step(4)
            action_items = be.extract_action_items(transcript)
            st.write("✅ Action items extracted")

            step(5)
            decisions = be.extract_key_decisions(transcript)
            st.write("✅ Key decisions found")

            step(6)
            questions = be.extract_questions(transcript)
            st.write("✅ Open questions collected")

            step(7)
            rag_chain = be.build_rag_chain(transcript)
            st.write("✅ Chat index ready")

            bar.progress(1.0, text="Done")
            status.update(label="Analysis complete", state="complete", expanded=False)
        except Exception:
            status.update(label="Something went wrong", state="error", expanded=True)
            raise

    return {
        "run_id": uuid.uuid4().hex[:8],
        "source_label": label,
        "title": title,
        "transcript": transcript.strip(),
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
        "chunks": len(chunks),
        "seconds": time.time() - started,
    }


def build_report(res: dict) -> str:
    return (
        f"# {res['title']}\n\n"
        f"_Source: {res['source_label']}_\n\n"
        f"## Summary\n{res['summary']}\n\n"
        f"## Action Items\n{res['action_items']}\n\n"
        f"## Key Decisions\n{res['key_decisions']}\n\n"
        f"## Open Questions\n{res['open_questions']}\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# UI pieces
# ─────────────────────────────────────────────────────────────────────────────
def stat_card(value: str, label: str) -> str:
    return f"<div class='stat'><div class='v'>{value}</div><div class='l'>{label}</div></div>"


def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown(BRAND_HTML, unsafe_allow_html=True)

        st.markdown("<div class='sec-label'>Source</div>", unsafe_allow_html=True)
        mode = st.radio("Source", ["YouTube link", "Upload file"], horizontal=True, label_visibility="collapsed")
        url, upload = "", None
        # Inside a form, pressing Enter in the box submits it, same as clicking the button
        with st.form("analyze_form", border=False, enter_to_submit=True):
            if mode == "YouTube link":
                url = st.text_input("YouTube URL", placeholder="Paste a YouTube link", label_visibility="collapsed")
            else:
                upload = st.file_uploader("Audio or video file", type=UPLOAD_TYPES, label_visibility="collapsed")
            go = st.form_submit_button("✨  Analyze video", type="primary")
        if st.session_state.get("result") is not None:
            if st.button("Start over"):
                st.session_state.result = None
                st.session_state.messages = []
                st.rerun()

        st.markdown(SIDEBAR_FEATURES_HTML, unsafe_allow_html=True)

    return {"mode": mode, "url": url.strip(), "upload": upload, "go": go}


def chat_panel(res: dict):
    be = load_backend()
    msgs = st.session_state.setdefault("messages", [])

    pending = st.session_state.pop("pending_q", None)
    box = st.container(key="card_chat")
    typed = st.chat_input("Ask anything about this video…")
    question = pending or typed

    with box:
        st.markdown("<div class='chat-hint'>Answers are grounded in this video's transcript only.</div>",
                    unsafe_allow_html=True)
        for m in msgs:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        if not msgs and not question:
            cols = st.columns(len(SUGGESTIONS))
            for i, (col, s) in enumerate(zip(cols, SUGGESTIONS)):
                if col.button(s, key=f"sugg_{i}"):
                    st.session_state["pending_q"] = s
                    st.rerun()

        if question:
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Searching the transcript…"):
                    try:
                        answer = be.ask_question(res["rag_chain"], question)
                    except Exception as e:  # noqa: BLE001
                        answer = f"⚠️ I couldn't answer that: {e}"
                st.markdown(answer)
            msgs.append({"role": "user", "content": question})
            msgs.append({"role": "assistant", "content": answer})


def render_results(res: dict):
    st.markdown(
        f"<div class='result-head'><div class='kicker'>Analysis ready</div>"
        f"<h2>{html.escape(res['title'])}</h2>"
        f"<div class='src'>{html.escape(res['source_label'])}</div></div>",
        unsafe_allow_html=True,
    )
    st.write("")

    words = len(res["transcript"].split())
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card(f"{words:,}", "Words spoken"), unsafe_allow_html=True)
    c2.markdown(stat_card(f"≈ {max(1, round(words / 150))} min", "Speaking time"), unsafe_allow_html=True)
    c3.markdown(stat_card(str(res["chunks"]), "Audio chunks"), unsafe_allow_html=True)
    c4.markdown(stat_card(f"{res['seconds']:.0f}s", "Processed in"), unsafe_allow_html=True)

    st.write("")
    d1, d2, _ = st.columns([1, 1, 3])
    d1.download_button("⬇  Report (.md)", build_report(res), file_name="video_report.md", mime="text/markdown")
    d2.download_button("⬇  Transcript (.txt)", res["transcript"], file_name="transcript.txt", mime="text/plain")
    st.write("")

    tabs = st.tabs(["📋 Summary", "✅ Action items", "🔑 Decisions", "❓ Open questions", "📝 Transcript", "💬 Chat"])
    with tabs[0]:
        with st.container(key="card_summary"):
            st.markdown(res["summary"])
    with tabs[1]:
        with st.container(key="card_actions"):
            st.markdown(res["action_items"])
    with tabs[2]:
        with st.container(key="card_decisions"):
            st.markdown(res["key_decisions"])
    with tabs[3]:
        with st.container(key="card_questions"):
            st.markdown(res["open_questions"])
    with tabs[4]:
        st.text_area("Transcript", res["transcript"], height=460,
                     key=f"tx_{res['run_id']}", label_visibility="collapsed")
    with tabs[5]:
        chat_panel(res)


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)
st.session_state.setdefault("result", None)
st.session_state.setdefault("messages", [])

inputs = render_sidebar()

if inputs["go"]:
    st.session_state.result = None
    st.session_state.messages = []

result = st.session_state.result

if result is None:
    st.markdown(HERO_HTML, unsafe_allow_html=True)

if inputs["go"]:
    st.write("")
    problem = None
    if inputs["mode"] == "YouTube link":
        if not inputs["url"].startswith(("http://", "https://")):
            problem = "Paste a valid YouTube link (starting with https://) in the sidebar."
        source, label = inputs["url"], inputs["url"]
    else:
        if inputs["upload"] is None:
            problem = "Upload an audio or video file in the sidebar first."
            source = label = ""
        else:
            source, label = save_upload(inputs["upload"]), inputs["upload"].name
    if not problem and not os.getenv("GROQ_API_KEY"):
        problem = "GROQ_API_KEY is missing. Add it to your .env file and restart the app."

    if problem:
        st.warning(problem)
    else:
        try:
            st.session_state.result = analyze(source, label)
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"{type(e).__name__}: {e}")
            with st.expander("Troubleshooting"):
                st.markdown(
                    "- Is **FFmpeg** installed and on your PATH? (`ffmpeg -version`)\n"
                    "- Is `GROQ_API_KEY` set correctly?\n"
                    "- Is the YouTube link public and reachable?\n"
                    "- Try a smaller Whisper model if memory runs out."
                )
elif result is not None:
    render_results(result)