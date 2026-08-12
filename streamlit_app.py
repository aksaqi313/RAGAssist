import os
import sys
import runpy
from pathlib import Path

import streamlit as st

# Define project paths
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
FRONTEND_APP = ROOT_DIR / "frontend" / "streamlit_app.py"

# Add src directory to Python path
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Pass Gemini API key from Streamlit Cloud Secrets into environment if set
try:
    if "GEMINI_API_KEY" in st.secrets and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# Execute the primary Streamlit application from frontend
runpy.run_path(str(FRONTEND_APP), run_name="__main__")
