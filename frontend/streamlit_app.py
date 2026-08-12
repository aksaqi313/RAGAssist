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

if "theme" not in st.session_state:
    st.session_state.theme = "dark"


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

theme_vars = f"""
    <style>
    :root {{
        --bg-color: {'#0E1117' if st.session_state.theme == 'dark' else '#F3F4F6'};
        --panel-bg: {'#161A23' if st.session_state.theme == 'dark' else '#FFFFFF'};
        --border-main: {'#262B3D' if st.session_state.theme == 'dark' else '#E5E7EB'};
        --border-panel: {'#2D3346' if st.session_state.theme == 'dark' else '#E5E7EB'};
        --text-title: {'#F8F9FA' if st.session_state.theme == 'dark' else '#111827'};
        --text-primary: {'#FFFFFF' if st.session_state.theme == 'dark' else '#1F2937'};
        --text-secondary: {'#8C92A4' if st.session_state.theme == 'dark' else '#4B5563'};
        --text-muted: {'#A3A8B8' if st.session_state.theme == 'dark' else '#6B7280'};
        --text-footer: {'#6B7280' if st.session_state.theme == 'dark' else '#9CA3AF'};
        --hover-bg: {'rgba(255, 255, 255, 0.05)' if st.session_state.theme == 'dark' else 'rgba(0, 0, 0, 0.05)'};
        --panel-bg-alpha: {'rgba(255, 255, 255, 0.03)' if st.session_state.theme == 'dark' else 'rgba(0, 0, 0, 0.02)'};
        --input-border: {'#374151' if st.session_state.theme == 'dark' else '#D1D5DB'};
        --hover-border: {'#4B5563' if st.session_state.theme == 'dark' else '#9CA3AF'};
        --hero-grad-1: {'#1A1D27' if st.session_state.theme == 'dark' else '#FFFFFF'};
        --hero-grad-2: {'#12151C' if st.session_state.theme == 'dark' else '#F9FAFB'};
        --workflow-grad: {'#11141A' if st.session_state.theme == 'dark' else '#F9FAFB'};
        --shadow-color: {'rgba(0, 0, 0, 0.1)' if st.session_state.theme == 'dark' else 'rgba(0, 0, 0, 0.05)'};
        --shadow-strong: {'rgba(0, 0, 0, 0.2)' if st.session_state.theme == 'dark' else 'rgba(0, 0, 0, 0.1)'};
    }}
    </style>
"""
st.markdown(theme_vars, unsafe_allow_html=True)

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* Clean Modern Theme */
    .stApp {
        background-color: var(--bg-color);
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
        color: var(--text-title) !important;
    }

    p, div, span, label {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Layout */
    section[data-testid="stSidebar"] {
        background: var(--panel-bg);
        border-right: 1px solid var(--border-main);
    }

    section[data-testid="stSidebar"] > div:first-child {
        height: 100vh;
        overflow-y: auto;
    }

    section[data-testid="stSidebar"] button {
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.2s ease;
    }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        background: transparent !important;
        color: #A3A8B8 !important;
        border: 1px solid transparent !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: var(--hover-bg) !important;
        color: var(--text-primary) !important;
    }

    section[data-testid="stSidebar"] button[kind="primary"] {
        background: #2563EB !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
    }

    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background: #1D4ED8 !important;
    }

    /* Sidebar Brand Header */
    .brand-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .brand-subtitle {
        font-size: 12px;
        color: #8C92A4;
        line-height: 1.4;
    }

    /* Sidebar Stats Box */
    .kb-mini {
        margin-top: 16px;
        padding: 14px;
        border-radius: 10px;
        background: var(--panel-bg-alpha);
        border: 1px solid var(--border-panel);
    }

    .kb-mini-label {
        font-size: 10px;
        color: #8C92A4;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .kb-mini-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }

    .kb-mini-value {
        font-size: 14px;
        font-weight: 700;
        color: #E2E8F0;
    }

    .kb-mini-name {
        font-size: 12px;
        color: #A3A8B8;
    }

    /* Hero Section */
    .hero {
        padding: 24px;
        border-radius: 12px;
        background: linear-gradient(145deg, var(--hero-grad-1) 0%, var(--hero-grad-2) 100%);
        border: 1px solid var(--border-panel);
        margin-bottom: 16px;
        box-shadow: 0 4px 12px var(--shadow-color);
    }

    .hero-eyebrow {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        color: #3B82F6;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        padding: 4px 10px;
        border-radius: 999px;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }

    .hero-title {
        font-size: 24px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 8px;
        line-height: 1.3;
    }

    .hero-subtitle {
        font-size: 14px;
        color: #A3A8B8;
        line-height: 1.5;
        max-width: 700px;
    }

    .hero-subtitle strong {
        color: #FFFFFF;
        font-weight: 600;
    }

    /* Status Card */
    .status-card {
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 13px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
    }

    .status-card.online {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #34D399;
    }

    .status-card.offline {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: #F87171;
    }

    /* Feature Cards */
    .feature-card {
        padding: 16px;
        border-radius: 10px;
        background: #161A23;
        border: 1px solid #2D3346;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 16px;
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .feature-card:hover {
        border-color: #3B82F6;
        transform: translateY(-2px);
    }

    .feature-title {
        display: flex;
        align-items: center;
        font-size: 13px;
        font-weight: 600;
        color: #F8F9FA;
        margin-bottom: 6px;
    }

    .feature-icon {
        font-size: 16px;
        margin-right: 8px;
    }

    .feature-text {
        font-size: 12px;
        color: #8C92A4;
        line-height: 1.4;
    }

    /* Panels */
    .panel {
        padding: 20px;
        border-radius: 12px;
        background: #161A23;
        border: 1px solid #2D3346;
        margin-bottom: 16px;
    }

    .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 4px;
    }

    .section-subtitle {
        font-size: 13px;
        color: #8C92A4;
        margin-bottom: 16px;
    }

    .workflow-panel {
        background: linear-gradient(180deg, var(--panel-bg) 0%, var(--workflow-grad) 100%) !important;
    }

    .workflow-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .workflow-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }

    .workflow-item-icon {
        width: 24px;
        height: 24px;
        border-radius: 6px;
        background: #2563EB;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        color: white;
        flex-shrink: 0;
        margin-top: 2px;
    }

    .workflow-item-title {
        font-size: 13px;
        font-weight: 600;
        color: #F8F9FA;
        margin-bottom: 2px;
    }

    .workflow-item-desc {
        font-size: 12px;
        color: #8C92A4;
        line-height: 1.4;
    }

    .kb-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid var(--border-panel);
    }

    .kb-row:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }

    .kb-doc-name {
        font-size: 13px;
        color: #FFFFFF;
        font-weight: 500;
    }

    .kb-doc-meta {
        font-size: 11px;
        color: #8C92A4;
        margin-top: 4px;
    }

    .kb-badge {
        display: inline-block;
        font-size: 10px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        background: rgba(52, 211, 153, 0.1);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.2);
    }

    .kb-badge.default {
        background: rgba(59, 130, 246, 0.1);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    .kb-stats-row {
        display: flex;
        justify-content: space-between;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border-panel);
    }

    .kb-stat {
        text-align: center;
        flex: 1;
    }

    .kb-stat-value {
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
    }

    .kb-stat-label {
        font-size: 10px;
        color: #8C92A4;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Ready Section */
    .ready-container {
        padding: 16px 20px;
        border-radius: 10px;
        background: #161A23;
        border: 1px solid #2D3346;
        border-left: 4px solid #2563EB;
    }

    .ready-eyebrow {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: #60A5FA;
        margin-bottom: 4px;
    }

    .ready-heading {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
    }

    /* Document Cards */
    .document-card {
        padding: 16px;
        border-radius: 10px;
        background: #161A23;
        border: 1px solid #2D3346;
        transition: border-color 0.2s;
    }
    
    .document-card:hover {
        border-color: var(--hover-border);
    }

    .document-name {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
    }

    .document-meta {
        font-size: 12px;
        color: #8C92A4;
    }

    /* Answer Box & Chat Messages */
    .answer-box {
        padding: 20px;
        border-radius: 12px;
        background: var(--panel-bg);
        border: 1px solid var(--border-panel);
        color: var(--text-title);
        line-height: 1.6;
        font-size: 14px;
    }

    [data-testid="stChatMessage"] {
        background: var(--panel-bg);
        border: 1px solid var(--border-panel);
        border-radius: 12px;
        padding: 12px;
    }

    .stMarkdown, .stCaption, label, .stTextInput label {
        color: var(--text-muted) !important;
    }

    /* ========================================================
       ULTRA-PROFESSIONAL SEARCH / CHAT INPUT BAR STYLING
       ======================================================== */

    div[data-testid="stBottomBlockContainer"],
    div[data-testid="stBottom"],
    div[data-testid*="Bottom"],
    .stChatFloatingInputContainer {
        background-color: var(--bg-color) !important;
        background: var(--bg-color) !important;
        border-top: 1px solid var(--border-panel) !important;
        padding-top: 16px !important;
        padding-bottom: 24px !important;
    }

    div[data-testid="stBottomBlockContainer"] *,
    div[data-testid="stBottom"] * {
        background-color: transparent !important;
    }

    div[data-testid="stChatInput"] {
        background: var(--panel-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stChatInput"]:focus-within {
        border-color: #3B82F6 !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15) !important;
    }

    div[data-testid="stChatInput"] textarea {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        background: transparent !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: var(--text-muted) !important;
        font-size: 14px !important;
    }

    div[data-testid="stChatInput"] button {
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        transition: background 0.2s !important;
    }

    div[data-testid="stChatInput"] button:hover {
        background: #1D4ED8 !important;
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
        color: var(--text-footer);
        font-size: 12px;
        padding: 20px 0 10px 0;
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

    st.write("")
    st.markdown('<div class="kb-mini-label" style="margin-top: 10px;">APPEARANCE</div>', unsafe_allow_html=True)
    is_dark = st.toggle("🌙 Dark Mode", value=(st.session_state.theme == "dark"))
    if is_dark and st.session_state.theme == "light":
        st.session_state.theme = "dark"
        st.rerun()
    elif not is_dark and st.session_state.theme == "dark":
        st.session_state.theme = "light"
        st.rerun()


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
                answer_stream, error = ask_question(question)

            if answer_stream is not None:
                def stream_data():
                    if isinstance(answer_stream, str):
                        yield answer_stream
                    else:
                        for chunk in answer_stream:
                            if chunk.text:
                                yield chunk.text
                
                # Streamlit's built-in fast streaming!
                answer = st.write_stream(stream_data())
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