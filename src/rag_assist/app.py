from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from rag_assist.rag import (
    generate_answer,
    load_document,
    get_document_info,
    get_all_documents,
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="RAG-Assist API",
    description="AI-powered document question answering using RAG",
    version="1.0.0",
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS_DIR = PROJECT_ROOT / "documents"

DOCUMENTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# REQUEST MODEL
# ============================================================

class QueryRequest(BaseModel):
    question: str


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "RAG-Assist API",
    }


# ============================================================
# QUERY
# ============================================================

@app.post("/query")
def query(request: QueryRequest):

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:

        answer = generate_answer(
            request.question
        )

        return {
            "question": request.question,
            "answer": answer,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided.",
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    # --------------------------------------------------------
    # Save PDF
    # --------------------------------------------------------

    file_path = DOCUMENTS_DIR / file.filename

    try:

        file_content = await file.read()

        with open(
            file_path,
            "wb",
        ) as output_file:

            output_file.write(file_content)

        # ----------------------------------------------------
        # Add document to RAG knowledge base
        # ----------------------------------------------------

        info = load_document(
            file_path,
            file.filename,
        )

        # ----------------------------------------------------
        # Get knowledge-base information
        # ----------------------------------------------------

        knowledge_base = get_document_info()

        return {
            "status": "success",
            "message": "Document uploaded successfully.",
            "document_name": file.filename,
            "chunks": info["chunks"],
            "vectors": info["vectors"],
            "total_documents": knowledge_base[
                "document_count"
            ],
            "total_chunks": knowledge_base[
                "total_chunks"
            ],
            "total_vectors": knowledge_base[
                "total_vectors"
            ],
        }

    except Exception as error:

        if file_path.exists():

            try:
                file_path.unlink()

            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# GET DOCUMENTS
# ============================================================

@app.get("/documents")
def get_documents():

    try:

        return {
            "status": "success",
            "documents": get_all_documents(),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# KNOWLEDGE BASE
# ============================================================

@app.get("/knowledge-base")
def knowledge_base():

    try:

        return {
            "status": "success",
            "knowledge_base": get_document_info(),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
