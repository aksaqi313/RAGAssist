import os
import sys
import html
from pathlib import Path

import streamlit as st

# Setup Python path so rag_assist module can be imported anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Load Gemini API key from Streamlit App Secrets if available
try:
    if "GEMINI_API_KEY" in st.secrets and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

try:
    from rag_assist.rag import (
        generate_answer,
        load_document,
        get_document_info,
        get_all_documents,
        delete_document as rag_delete_document,
        DOCUMENTS_DIR,
    )
    RAG_IMPORT_ERROR = None
except Exception as err:
    RAG_IMPORT_ERROR = str(err)



# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="RAG-Assist | AI Document Knowledge Assistant",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_DOCUMENT = "AI_ML_Sample_Document.pdf"


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_page" not in st.session_state:
    st.session_state.active_page = "Home"


# ============================================================
# RAG ENGINE WRAPPERS
# (formerly HTTP calls to FastAPI — now direct function calls)
# ============================================================

def get_documents():
    """Get all documents currently stored in the knowledge base."""
    try:
        return get_all_documents(), None
    except Exception as error:
        return [], str(error)


def delete_document(document_id):
    """Delete a document from the knowledge base."""
    try:
        result = rag_delete_document(document_id)
        return True, result
    except Exception as error:
        return False, str(error)


def engine_ready():
    """Check whether the embedded RAG engine and API key are ready."""
    return RAG_IMPORT_ERROR is None and bool(os.getenv("GEMINI_API_KEY"))


def ask_question(question_text):
    """Run a question through the RAG engine and return the answer text."""
    try:
        answer = generate_answer(question_text)
        return answer, None
    except Exception as error:
        return None, str(error)


def upload_and_process(uploaded_file):
    """Save an uploaded PDF to disk and add it to the knowledge base."""
    file_path = DOCUMENTS_DIR / uploaded_file.name

    try:
        with open(file_path, "wb") as output_file:
            output_file.write(uploaded_file.getvalue())

        info = load_document(file_path, uploaded_file.name)
        knowledge_base = get_document_info()

        return {
            "document_name": uploaded_file.name,
            "chunks": info["chunks"],
            "vectors": info["vectors"],
            "total_documents": knowledge_base["document_count"],
            "total_chunks": knowledge_base["total_chunks"],
            "total_vectors": knowledge_base["total_vectors"],
        }, None

    except Exception as error:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        return None, str(error)


# ============================================================
# DESIGN SYSTEM & STYLING
# ============================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* Global Cosmic Background */
    .stApp {
        background-color: #0A0C1F;
        background-image:
            radial-gradient(1.5px 1.5px at 20px 30px, rgba(255,255,255,0.7), transparent),
            radial-gradient(1px 1px at 90px 70px, rgba(255,255,255,0.5), transparent),
            radial-gradient(circle at 15% 0%, #241a52 0%, transparent 45%),
            radial-gradient(circle at 100% 15%, #16264a 0%, transparent 42%),
            linear-gradient(180deg, #07081A 0%, #0A0C1F 55%, #0D0E24 100%);
        background-attachment: fixed;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1200px;
        margin: 0 auto;
        padding-top: 1.2rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    h1, h2, h3, .hero-title, .section-title {
        font-family: 'Space Grotesk', sans-serif !important;
    }

    p, div, span, label {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Layout */
    section[data-testid="stSidebar"] {
        background: #10122A;
        border-right: 1px solid rgba(139, 92, 246, 0.15);
    }

    section[data-testid="stSidebar"] > div:first-child {
        height: 100vh;
        overflow-y: auto;
    }

    section[data-testid="stSidebar"] button {
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 0.5rem 0.9rem !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        background: transparent !important;
        color: #B8B8D1 !important;
        border: 1px solid transparent !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(139, 92, 246, 0.12) !important;
        color: #E9E7FF !important;
    }

    section[data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(90deg, #6D28D9, #9333EA) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    }

    /* Sidebar Brand Header */
    .brand-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 22px;
        font-weight: 700;
        background: linear-gradient(90deg, #A78BFA, #60A5FA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }

    .brand-subtitle {
        font-size: 11px;
        color: #7C7C9E;
        line-height: 1.3;
    }

    /* Sidebar Stats Box */
    .kb-mini {
        margin-top: 14px;
        padding: 12px 14px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(109,40,217,0.18), rgba(59,130,246,0.10));
        border: 1px solid rgba(139, 92, 246, 0.25);
    }

    .kb-mini-label {
        font-size: 10px;
        color: #A5A0C7;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
        font-weight: 600;
    }

    .kb-mini-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }

    .kb-mini-value {
        font-size: 15px;
        font-weight: 700;
        color: #F1F0FF;
    }

    .kb-mini-name {
        font-size: 11.5px;
        color: #9C99C2;
    }

    /* Hero Section */
    .hero {
        padding: 14px 20px;
        border-radius: 14px;
        background:
            radial-gradient(circle at 88% 15%, rgba(139, 92, 246, 0.35), transparent 42%),
            linear-gradient(135deg, #0C0E24 0%, #171A3D 55%, #241B4D 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        margin-bottom: 12px;
    }

    .hero-eyebrow {
        display: inline-block;
        font-size: 10.5px;
        font-weight: 600;
        color: #C4B5FD;
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.3);
        padding: 2px 8px;
        border-radius: 999px;
        margin-bottom: 6px;
    }

    .hero-title {
        font-size: 19px;
        font-weight: 700;
        color: #F5F4FF;
        margin-bottom: 4px;
        line-height: 1.25;
    }

    .hero-subtitle {
        font-size: 12px;
        color: #B7B4D8;
        line-height: 1.4;
        max-width: 680px;
    }

    .hero-subtitle strong {
        color: #C4B5FD;
    }

    /* Status Card */
    .status-card {
        padding: 8px 14px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 12px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
    }

    .status-card.online {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(52, 211, 153, 0.35);
        color: #6EE7B7;
    }

    .status-card.offline {
        background: rgba(244, 63, 94, 0.10);
        border: 1px solid rgba(244, 63, 94, 0.35);
        color: #FCA5A5;
    }

    /* Feature Cards */
    .feature-card {
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(139, 92, 246, 0.18);
        min-height: 60px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 12px;
    }

    .feature-title {
        display: flex;
        align-items: center;
        font-size: 12px;
        font-weight: 600;
        color: #EDEBFF;
        margin-bottom: 2px;
    }

    .feature-icon {
        font-size: 13px;
        margin-right: 5px;
    }

    .feature-text {
        font-size: 10.5px;
        color: #9C99C2;
        line-height: 1.25;
    }

    /* Panels */
    .panel {
        padding: 14px 16px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(139, 92, 246, 0.20);
        box-sizing: border-box;
        margin-bottom: 12px;
    }

    .section-title {
        font-size: 14px;
        font-weight: 700;
        color: #F1F0FF;
        margin-bottom: 2px;
    }

    .section-subtitle {
        font-size: 11px;
        color: #8B87AD;
        margin-bottom: 8px;
    }

    .workflow-panel {
        background:
            radial-gradient(ellipse at 25% 15%, rgba(168, 85, 247, 0.20), transparent 55%),
            rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(168, 85, 247, 0.25) !important;
    }

    .workflow-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .workflow-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .workflow-item-icon {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        color: white;
        flex-shrink: 0;
    }

    .workflow-item-title {
        font-size: 11px;
        font-weight: 600;
        color: #E4E2FA;
    }

    .workflow-item-desc {
        font-size: 10.5px;
        color: #85819F;
    }

    .kb-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid rgba(139, 92, 246, 0.10);
    }

    .kb-row:last-child {
        border-bottom: none;
    }

    .kb-doc-name {
        font-size: 11.5px;
        color: #E4E2FA;
        font-weight: 500;
    }

    .kb-doc-meta {
        font-size: 10px;
        color: #7C7C9E;
    }

    .kb-badge {
        display: inline-block;
        font-size: 9.5px;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 999px;
        background: rgba(52, 211, 153, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }

    .kb-badge.default {
        background: rgba(96, 165, 250, 0.15);
        color: #93C5FD;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }

    .kb-stats-row {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(139, 92, 246, 0.15);
    }

    .kb-stat {
        text-align: center;
        flex: 1;
    }

    .kb-stat-value {
        font-size: 15px;
        font-weight: 700;
        color: #F1F0FF;
    }

    .kb-stat-label {
        font-size: 9px;
        color: #7C7C9E;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Ready Section */
    .ready-container {
        padding: 12px 18px;
        border-radius: 12px;
        background: linear-gradient(120deg, #14163A 0%, #1B1450 100%);
        border: 1px solid rgba(168, 85, 247, 0.30);
    }

    .ready-eyebrow {
        font-size: 9.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #93C5FD;
        margin-bottom: 2px;
    }

    .ready-heading {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 14px;
        font-weight: 700;
        color: #F5F4FF;
    }

    .ready-heading span {
        background: linear-gradient(90deg, #C4B5FD, #93C5FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Document Cards */
    .document-card {
        padding: 12px 14px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(139, 92, 246, 0.18);
    }

    .document-name {
        font-size: 13.5px;
        font-weight: 600;
        color: #EDEBFF;
    }

    .document-meta {
        font-size: 11px;
        color: #8B87AD;
        margin-top: 2px;
    }

    /* Answer Box & Chat Messages */
    .answer-box {
        padding: 16px 18px;
        border-radius: 14px;
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.25);
        color: #E4E2FA;
        line-height: 1.6;
    }

    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(139, 92, 246, 0.12);
        border-radius: 12px;
        margin-bottom: 8px;
    }

    .stMarkdown, .stCaption, label, .stTextInput label {
        color: #C7C4E0 !important;
    }

    /* ========================================================
       ULTRA-PROFESSIONAL SEARCH / CHAT INPUT BAR STYLING
       ======================================================== */

    div[data-testid="stBottomBlockContainer"],
    div[data-testid="stBottom"],
    div[data-testid*="Bottom"],
    .stChatFloatingInputContainer {
        background-color: #0A0C1F !important;
        background: #0A0C1F !important;
        border-top: 1px solid rgba(139, 92, 246, 0.20) !important;
        padding-top: 10px !important;
        padding-bottom: 14px !important;
    }

    div[data-testid="stBottomBlockContainer"] *,
    div[data-testid="stBottom"] * {
        background-color: transparent !important;
    }

    div[data-testid="stChatInput"] {
        background: rgba(20, 22, 50, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(139, 92, 246, 0.35) !important;
        border-radius: 14px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37), 0 0 15px rgba(139, 92, 246, 0.15) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stChatInput"]:focus-within {
        border-color: rgba(167, 139, 250, 0.85) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 25px rgba(139, 92, 246, 0.35) !important;
    }

    div[data-testid="stChatInput"] textarea {
        color: #F1F0FF !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13.5px !important;
        background: transparent !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #8B87AD !important;
        font-size: 13.5px !important;
    }

    div[data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #6D28D9 0%, #9333EA 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(147, 51, 234, 0.4) !important;
    }

    div[data-testid="stChatInput"] button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 4px 14px rgba(147, 51, 234, 0.6) !important;
    }

    div[data-testid="stChatInput"] button svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    .footer {
        text-align: center;
        color: #5C597A;
        font-size: 11px;
        padding: 16px 0 8px 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD KNOWLEDGE BASE (SHARED DATA)
# ============================================================

documents, documents_error = get_documents()

document_count = len(documents)
total_chunks = 0
total_vectors = 0

for document in documents:
    if isinstance(document, dict):
        total_chunks += document.get("chunks", 0)
        total_vectors += document.get("vectors", 0)


# ============================================================
# SIDEBAR — BRAND + NAVIGATION (INDEPENDENT SCROLL)
# ============================================================

NAV_ITEMS = [
    ("Home", "🏠"),
    ("Ask Question", "💬"),
    ("Knowledge Base", "📚"),
    ("Upload Document", "📤"),
    ("Manage Documents", "🗂️"),
    ("Settings", "⚙️"),
]

with st.sidebar:
    st.markdown(
        '<div class="brand-title">🤖 RAG-Assist</div>'
        '<div class="brand-subtitle">AI-Powered Document Knowledge Assistant</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    for label, icon in NAV_ITEMS:
        is_active = st.session_state.active_page == label
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{label}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.active_page = label
            st.rerun()

    st.markdown(
        '<div class="kb-mini">'
        '<div class="kb-mini-label">Active Knowledge Base</div>'
        f'<div class="kb-mini-row"><span class="kb-mini-name">Documents</span>'
        f'<span class="kb-mini-value">{document_count}</span></div>'
        f'<div class="kb-mini-row"><span class="kb-mini-name">Total Chunks</span>'
        f'<span class="kb-mini-value">{total_chunks}</span></div>'
        f'<div class="kb-mini-row"><span class="kb-mini-name">Embeddings</span>'
        f'<span class="kb-mini-value">{total_vectors}</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# SHARED: ENGINE STATUS BANNER
# ============================================================

def render_backend_status():
    if engine_ready():
        st.markdown(
            '<div class="status-card online">'
            '🟢 RAG Engine Ready &nbsp;•&nbsp; Embeddings + FAISS + Gemini running in-process'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        err_msg = RAG_IMPORT_ERROR or "GEMINI_API_KEY missing. Please add GEMINI_API_KEY to Streamlit Secrets."
        st.markdown(
            f'<div class="status-card offline">'
            f'⚠️ RAG Engine Action Required &nbsp;•&nbsp; {html.escape(err_msg)}'
            '</div>',
            unsafe_allow_html=True,
        )

    if documents_error:
        st.warning(f"⚠️ Could not load knowledge base: {documents_error}")


# ============================================================
# SHARED: DOCUMENT LIST
# ============================================================

def render_document_list(show_delete=True):
    if not documents:
        st.info("📭 Your knowledge base is currently empty.")
        return

    for document in documents:
        if not isinstance(document, dict):
            continue

        document_id = document.get("id")
        filename = document.get("filename", "Unknown document")
        uploaded_at = document.get("uploaded_at", "Unknown")
        chunks = document.get("chunks", 0)
        vectors = document.get("vectors", 0)

        left, middle, right = st.columns([5, 2, 1.2], vertical_alignment="center")

        with left:
            safe_filename = html.escape(filename)
            st.markdown(
                '<div class="document-card">'
                f'<div class="document-name">📄 {safe_filename}</div>'
                '<div class="document-meta">'
                f'Uploaded: {uploaded_at} &nbsp;•&nbsp; '
                f'Chunks: {chunks} &nbsp;•&nbsp; '
                f'Vectors: {vectors}'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        with middle:
            if filename == DEFAULT_DOCUMENT:
                st.success("Default Document")
            else:
                st.info("Active")

        with right:
            if not show_delete:
                continue

            if filename == DEFAULT_DOCUMENT:
                st.button(
                    "🔒 Locked",
                    key=f"protected_{document_id}",
                    disabled=True,
                    help="Default AI/ML document cannot be deleted.",
                    use_container_width=True,
                )
            elif document_id is not None:
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{document_id}",
                    help=f"Delete {filename}",
                    use_container_width=True,
                ):
                    with st.spinner(f"Deleting {filename}..."):
                        success, result = delete_document(document_id)

                    if success:
                        st.success(f"Deleted {filename}")
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {result}")


# ============================================================
# PAGE: HOME
# ============================================================

def render_home():
    # 1. Hero Section
    st.markdown(
        '<div class="hero">'
        '<div class="hero-eyebrow">✨ Welcome back</div>'
        '<div class="hero-title">Let\'s unlock the power of your documents.</div>'
        '<div class="hero-subtitle">'
        'Upload. Understand. Ask. Get <strong>intelligent answers</strong> '
        'grounded in your own PDFs — powered by FAISS retrieval and Gemini generation.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # 2. Engine Status Card
    render_backend_status()

    # 3. 4 Feature Cards
    feature_cols = st.columns(4)
    features = [
        ("☁️", "Upload Documents", "Upload your PDFs and more."),
        ("🧩", "Build Knowledge", "Automatic embedding creation."),
        ("💬", "Ask Anything", "Natural language Q&A."),
        ("✨", "Get Answers", "Context-aware AI answers."),
    ]

    for col, (icon, title, text) in zip(feature_cols, features):
        with col:
            st.markdown(
                '<div class="feature-card">'
                f'<div class="feature-title"><span class="feature-icon">{icon}</span>{title}</div>'
                f'<div class="feature-text">{text}</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # 4. Main Information Area (Side-by-Side: How Mini-RAG Works + Your Knowledge Base)
    workflow_col, kb_col = st.columns([3, 2], gap="medium")

    with workflow_col:
        steps = [
            ("01", "📤", "Upload Documents", "Upload PDFs, DOCX, TXT files.", "#8B5CF6"),
            ("02", "📄", "Extract Text", "Extract and clean raw text.", "#3B82F6"),
            ("03", "🧩", "Chunk Text", "Split into semantically relevant chunks.", "#10B981"),
            ("04", "🧠", "Generate Embeddings", "Create vector representations.", "#A78BFA"),
            ("05", "🗄️", "Store in FAISS", "Index vectors for instant retrieval.", "#F59E0B"),
            ("06", "🔎", "Retrieve & Answer", "Fetch relevant context & answer.", "#F43F5E"),
        ]

        step_html = (
            '<div class="panel workflow-panel">'
            '<div class="section-title">🧭 How Mini-RAG Works</div>'
            '<div class="section-subtitle">From raw documents to intelligent answers</div>'
            '<div class="workflow-list">'
        )

        for num, icon, title, desc, color in steps:
            step_html += (
                '<div class="workflow-item">'
                f'<div class="workflow-item-icon" style="background:{color};">{icon}</div>'
                f'<div><span class="workflow-item-title">{num}. {title}</span> '
                f'<span class="workflow-item-desc">— {desc}</span></div>'
                '</div>'
            )

        step_html += '</div></div>'
        st.markdown(step_html, unsafe_allow_html=True)

    with kb_col:
        kb_html = (
            '<div class="panel kb-panel">'
            '<div class="section-title">📚 Your Knowledge Base</div>'
            '<div class="section-subtitle">Live active document summary</div>'
        )

        if documents:
            for document in documents[:3]:
                if not isinstance(document, dict):
                    continue

                filename = html.escape(document.get("filename", "Unknown"))
                chunks = document.get("chunks", 0)
                is_default = document.get("filename") == DEFAULT_DOCUMENT
                badge_class = "default" if is_default else ""
                badge_text = "Default" if is_default else "Active"

                kb_html += (
                    '<div class="kb-row">'
                    f'<div><div class="kb-doc-name">📄 {filename}</div>'
                    f'<div class="kb-doc-meta">{chunks} chunks</div></div>'
                    f'<span class="kb-badge {badge_class}">{badge_text}</span>'
                    '</div>'
                )
        else:
            kb_html += (
                '<div style="padding: 10px 0; color: #85819F; font-size: 11.5px;">'
                '📬 No documents yet — upload one to get started.'
                '</div>'
            )

        kb_html += (
            '<div class="kb-stats-row">'
            f'<div class="kb-stat"><div class="kb-stat-value">{document_count}</div>'
            '<div class="kb-stat-label">Docs</div></div>'
            f'<div class="kb-stat"><div class="kb-stat-value">{total_chunks}</div>'
            '<div class="kb-stat-label">Chunks</div></div>'
            f'<div class="kb-stat"><div class="kb-stat-value">{total_vectors}</div>'
            '<div class="kb-stat-label">Vectors</div></div>'
            '<div class="kb-stat"><div class="kb-stat-value">FAISS</div>'
            '<div class="kb-stat-label">DB</div></div>'
            '</div>'
            '</div>'
        )

        st.markdown(kb_html, unsafe_allow_html=True)

    # 5. Ready Section & Action Buttons
    ready_col1, ready_col2, ready_col3 = st.columns([2.6, 1, 1], vertical_alignment="center")

    with ready_col1:
        st.markdown(
            '<div class="ready-container">'
            '<div class="ready-eyebrow">Ready when you are</div>'
            '<div class="ready-heading">Jump into a <span>conversation</span> with your documents</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with ready_col2:
        if st.button("💬 Start Asking", use_container_width=True, type="primary"):
            st.session_state.active_page = "Ask Question"
            st.rerun()

    with ready_col3:
        if st.button("📤 Upload PDF", use_container_width=True):
            st.session_state.active_page = "Upload Document"
            st.rerun()


# ============================================================
# PAGE: ASK QUESTION (SCROLLABLE CHAT HISTORY)
# ============================================================

def render_ask_question():
    st.markdown(
        '<div class="section-title">💬 Ask Your AI Assistant</div>'
        '<div class="section-subtitle">'
        'Ask questions grounded in your active documents or general AI topics.'
        '</div>',
        unsafe_allow_html=True,
    )

    render_backend_status()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask something about your documents, AI, Machine Learning...",
        key="ask_page_chat_input",
    )

    if question:
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("🔎 Searching knowledge base and generating answer..."):
                answer, error = ask_question(question)

            if answer is not None:
                st.markdown(
                    f'<div class="answer-box">{html.escape(answer)}</div>',
                    unsafe_allow_html=True,
                )
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"❌ {error}")


# ============================================================
# PAGE: KNOWLEDGE BASE
# ============================================================

def render_knowledge_base():
    st.markdown(
        '<div class="section-title">📚 Knowledge Base</div>'
        '<div class="section-subtitle">'
        'All documents active in your vector store.'
        '</div>',
        unsafe_allow_html=True,
    )

    render_backend_status()

    render_document_list(show_delete=True)

    st.write("")

    if st.button("🔄 Refresh Knowledge Base", use_container_width=True):
        st.rerun()


# ============================================================
# PAGE: UPLOAD DOCUMENT
# ============================================================

def render_upload_document():
    st.markdown(
        '<div class="section-title">📤 Upload Document</div>'
        '<div class="section-subtitle">'
        'Upload a PDF to permanently add it to your knowledge base.'
        '</div>',
        unsafe_allow_html=True,
    )

    render_backend_status()

    uploaded_file = st.file_uploader(
        "Choose a PDF document",
        type=["pdf"],
        help="Upload a PDF document to expand your RAG knowledge base.",
    )

    if uploaded_file is not None:
        st.info(f"📄 Selected document: **{uploaded_file.name}**")

        if st.button(
            "🚀 Upload & Process Document",
            use_container_width=True,
            type="primary",
        ):
            with st.spinner(
                "Extracting text, creating embeddings, and updating FAISS index..."
            ):
                data, error = upload_and_process(uploaded_file)

            if data is not None:
                st.success("✅ Document uploaded successfully!")

                st.info(
                    f"📄 **Document:** {data['document_name']}  \n"
                    f"🧩 **Chunks:** {data['chunks']}  \n"
                    f"🔎 **Vectors:** {data['vectors']}  \n"
                    f"📚 **Total Documents:** {data['total_documents']}"
                )
                st.rerun()
            else:
                st.error("❌ Upload failed.")
                st.caption(error)


# ============================================================
# PAGE: MANAGE DOCUMENTS
# ============================================================

def render_manage_documents():
    st.markdown(
        '<div class="section-title">🗂️ Manage Documents</div>'
        '<div class="section-subtitle">'
        'Review and delete documents from your active knowledge base.'
        '</div>',
        unsafe_allow_html=True,
    )

    render_backend_status()

    render_document_list(show_delete=True)


# ============================================================
# PAGE: SETTINGS
# ============================================================

def render_settings():
    st.markdown(
        '<div class="section-title">⚙️ Settings</div>'
        '<div class="section-subtitle">'
        'System configuration and workspace reset.'
        '</div>',
        unsafe_allow_html=True,
    )

    render_backend_status()

    st.markdown(
        '<div class="panel">'
        '<div class="section-title" style="font-size:14px;">Deployment Mode</div>'
        '<div class="section-subtitle" style="margin-bottom:0;">'
        'Embedded — the RAG engine runs in the same process as this Streamlit app '
        '(no separate FastAPI server required).'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="panel">'
        '<div class="section-title" style="font-size:14px;">AI Pipeline</div>'
        '<div class="section-subtitle" style="margin-bottom:0;">'
        'Sentence Transformers → FAISS Vector Search → Gemini Generation'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ============================================================
# ROUTER
# ============================================================

PAGES = {
    "Home": render_home,
    "Ask Question": render_ask_question,
    "Knowledge Base": render_knowledge_base,
    "Upload Document": render_upload_document,
    "Manage Documents": render_manage_documents,
    "Settings": render_settings,
}

PAGES[st.session_state.active_page]()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="footer">'
    'Mini-RAG • Streamlit • FAISS • Sentence Transformers • Gemini'
    '</div>',
    unsafe_allow_html=True,
)