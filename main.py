import subprocess
import sys
import os

def main():
    print("Starting RAG-Assist...")
    
    # Ensure the src directory is in the PYTHONPATH so module imports work correctly
    env = os.environ.copy()
    src_path = os.path.abspath("src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_path
        
    try:
        # Run streamlit as a python module to ensure it uses the current python environment
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py"],
            env=env,
            check=True
        )
    except KeyboardInterrupt:
        print("\nShutting down RAG-Assist...")
    except subprocess.CalledProcessError as e:
        print(f"\nError starting RAG-Assist: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
