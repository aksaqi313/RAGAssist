from pathlib import Path
import os
import sqlite3
from datetime import datetime

import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from google import genai


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES & GEMINI CLIENT
# ============================================================

load_dotenv()

def get_gemini_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                key = st.secrets["GEMINI_API_KEY"]
                os.environ["GEMINI_API_KEY"] = key
        except Exception:
            pass
    return key

GEMINI_API_KEY = get_gemini_api_key()

client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as err:
        print(f"Warning: Could not initialize Gemini client: {err}")

def get_client():
    global client
    if client is not None:
        return client
    key = get_gemini_api_key()
    if not key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Please set GEMINI_API_KEY in your .env file or Streamlit App Secrets."
        )
    client = genai.Client(api_key=key)
    return client



# ============================================================
# 3. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS_DIR = PROJECT_ROOT / "documents"

DATA_DIR = PROJECT_ROOT / "data"

DATABASE_PATH = DATA_DIR / "documents.db"

DEFAULT_PDF_PATH = (
    DOCUMENTS_DIR
    / "AI_ML_Sample_Document.pdf"
)

# Create folders if they don't exist
DOCUMENTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 4. LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# ============================================================
# 5. GLOBAL RAG STATE
# ============================================================

# One FAISS index for ALL documents

index = None

# All chunks from all documents

chunks = []

# Document name corresponding to each chunk

chunk_sources = []

# List of documents currently available

documents = []


# ============================================================
# 6. DATABASE
# ============================================================

def initialize_database():
    """
    Create the SQLite database and documents table.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            uploaded_at TEXT NOT NULL,
            chunks INTEGER DEFAULT 0,
            vectors INTEGER DEFAULT 0
        )
        """
    )

    connection.commit()

    connection.close()


initialize_database()


# ============================================================
# 7. REGISTER DOCUMENT IN DATABASE
# ============================================================

def register_document(
    filename,
    chunk_count,
    vector_count
):
    """
    Add or update a document in the database.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents (
            filename,
            uploaded_at,
            chunks,
            vectors
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(filename)
        DO UPDATE SET
            chunks = excluded.chunks,
            vectors = excluded.vectors
        """,
        (
            filename,
            datetime.now().isoformat(),
            chunk_count,
            vector_count
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# 8. GET ALL DOCUMENTS FROM DATABASE
# ============================================================

def get_all_documents():
    """
    Return all documents stored in the database.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            uploaded_at,
            chunks,
            vectors
        FROM documents
        ORDER BY id ASC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    result = []

    for row in rows:

        result.append(
            {
                "id": row[0],
                "filename": row[1],
                "uploaded_at": row[2],
                "chunks": row[3],
                "vectors": row[4],
            }
        )

    return result


# ============================================================
# 9. DELETE DOCUMENT FROM DATABASE
# ============================================================

def delete_document(document_id):
    """
    Delete a user-uploaded document completely.

    This removes:
    - the database record
    - the PDF file
    - its chunks from the RAG memory
    - its vectors from the FAISS index

    The built-in AI/ML document is protected because it is
    the default knowledge source.
    """

    global chunks
    global chunk_sources
    global documents
    global index

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT filename
        FROM documents
        WHERE id = ?
        """,
        (document_id,)
    )

    row = cursor.fetchone()

    if not row:
        connection.close()

        raise ValueError(
            "Document not found."
        )

    filename = row[0]

    # Never delete the built-in base document.
    if filename == "AI_ML_Sample_Document.pdf":
        connection.close()

        raise ValueError(
            "The built-in AI/ML knowledge document "
            "cannot be deleted."
        )

    # Delete database record.
    cursor.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        """,
        (document_id,)
    )

    connection.commit()
    connection.close()

    # Remove the PDF from disk.
    file_path = DOCUMENTS_DIR / filename

    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as error:
            print(
                f"Warning: could not delete PDF file "
                f"{filename}: {error}"
            )

    # Remove all chunks belonging to this document.
    remaining_chunks = []
    remaining_sources = []

    for chunk, source_name in zip(
        chunks,
        chunk_sources
    ):
        if source_name != filename:
            remaining_chunks.append(chunk)
            remaining_sources.append(source_name)

    chunks = remaining_chunks
    chunk_sources = remaining_sources

    # Remove the document from the in-memory document list.
    documents = [
        document
        for document in documents
        if document != filename
    ]

    # Rebuild FAISS using the remaining documents.
    if chunks:
        rebuild_faiss_index()
    else:
        index = None

    print(
        f"Document deleted successfully: "
        f"{filename}"
    )

    return {
        "document_id": document_id,
        "filename": filename,
        "remaining_documents": len(documents),
        "remaining_chunks": len(chunks),
        "remaining_vectors": (
            index.ntotal
            if index
            else 0
        ),
    }


# ============================================================
# 10. EXTRACT TEXT FROM PDF
# ============================================================

def extract_pdf_text(pdf_path):
    """
    Extract text from a PDF file.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found at: {pdf_path}"
        )

    reader = PdfReader(
        str(pdf_path)
    )

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    if not text.strip():
        raise ValueError(
            "No readable text was extracted from the PDF."
        )

    return text


# ============================================================
# 11. CREATE TEXT CHUNKS
# ============================================================

def create_chunks(
    text,
    chunk_size=500
):
    """
    Split document text into smaller chunks.
    """

    words = text.split()

    chunks_list = []

    for i in range(
        0,
        len(words),
        chunk_size
    ):

        chunk = " ".join(
            words[
                i:i + chunk_size
            ]
        )

        if chunk.strip():

            chunks_list.append(
                chunk
            )

    return chunks_list


# ============================================================
# 12. CREATE EMBEDDINGS
# ============================================================

def create_embeddings(
    chunks_list
):
    """
    Create vector embeddings for chunks.
    """

    if not chunks_list:

        raise ValueError(
            "Cannot create embeddings "
            "because no chunks exist."
        )

    print(
        f"Creating embeddings for "
        f"{len(chunks_list)} chunks..."
    )

    embeddings = embedding_model.encode(
        chunks_list,
        convert_to_numpy=True
    )

    return embeddings.astype(
        "float32"
    )


# ============================================================
# 13. REBUILD COMPLETE FAISS INDEX
# ============================================================

def rebuild_faiss_index():
    """
    Rebuild one FAISS index containing
    chunks from ALL available documents.
    """

    global index

    if not chunks:

        raise ValueError(
            "No document chunks available."
        )

    print(
        f"Rebuilding FAISS index "
        f"with {len(chunks)} chunks..."
    )

    embeddings = create_embeddings(
        chunks
    )

    index = faiss.IndexFlatL2(
        embeddings.shape[1]
    )

    index.add(
        embeddings
    )

    print(
        f"FAISS index created with "
        f"{index.ntotal} vectors."
    )


# ============================================================
# 14. LOAD DOCUMENT INTO KNOWLEDGE BASE
# ============================================================

def load_document(
    pdf_path,
    document_name=None
):
    """
    Add a PDF to the shared RAG knowledge base.

    A new document is added to the existing knowledge base.
    If the same filename already exists, its old chunks are
    replaced instead of duplicated.
    """

    global chunks
    global chunk_sources
    global documents

    pdf_path = Path(
        pdf_path
    )

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found at: {pdf_path}"
        )

    if document_name:
        final_name = document_name
    else:
        final_name = pdf_path.name

    print(
        f"Loading document: {final_name}"
    )

    # --------------------------------------------------------
    # Extract PDF text
    # --------------------------------------------------------

    text = extract_pdf_text(
        pdf_path
    )

    # --------------------------------------------------------
    # Create chunks
    # --------------------------------------------------------

    print(
        "Creating document chunks..."
    )

    new_chunks = create_chunks(
        text
    )

    if not new_chunks:
        raise ValueError(
            "No text chunks were created "
            "from the PDF."
        )

    print(
        f"Created {len(new_chunks)} chunks."
    )

    # --------------------------------------------------------
    # Remove old chunks for this filename if it already exists.
    # --------------------------------------------------------

    remaining_chunks = []
    remaining_sources = []

    for chunk, source_name in zip(
        chunks,
        chunk_sources
    ):
        if source_name != final_name:
            remaining_chunks.append(chunk)
            remaining_sources.append(source_name)

    chunks = remaining_chunks
    chunk_sources = remaining_sources

    # --------------------------------------------------------
    # Add the new version.
    # --------------------------------------------------------

    chunks.extend(
        new_chunks
    )

    chunk_sources.extend(
        [final_name] * len(new_chunks)
    )

    # Add document to the in-memory document list.
    if final_name not in documents:
        documents.append(
            final_name
        )

    # --------------------------------------------------------
    # Rebuild FAISS with ALL documents.
    # --------------------------------------------------------

    rebuild_faiss_index()

    # --------------------------------------------------------
    # Store document information in SQLite.
    # --------------------------------------------------------

    register_document(
        filename=final_name,
        chunk_count=len(new_chunks),
        vector_count=len(new_chunks)
    )

    print(
        f"Document added successfully: "
        f"{final_name}"
    )

    print(
        f"Total documents: "
        f"{len(documents)}"
    )

    print(
        f"Total chunks: "
        f"{len(chunks)}"
    )

    return {
        "document_name": final_name,
        "chunks": len(new_chunks),
        "vectors": len(new_chunks),
        "total_documents": len(documents),
        "total_chunks": len(chunks),
    }


# ============================================================
# 15. LOAD EXISTING DOCUMENTS FROM DISK
# ============================================================

def load_existing_documents():
    """
    Load all PDFs from the documents folder
    into the RAG knowledge base.
    """

    global chunks
    global chunk_sources
    global documents
    global index

    # Reset memory

    chunks = []

    chunk_sources = []

    documents = []

    index = None

    print(
        "Loading documents from knowledge base..."
    )

    pdf_files = list(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    if not pdf_files:

        print(
            "No PDF documents found."
        )

        return

    for pdf_path in pdf_files:

        try:

            print(
                f"Processing: "
                f"{pdf_path.name}"
            )

            text = extract_pdf_text(
                pdf_path
            )

            document_chunks = create_chunks(
                text
            )

            if not document_chunks:

                continue

            chunks.extend(
                document_chunks
            )

            chunk_sources.extend(
                [pdf_path.name]
                * len(document_chunks)
            )

            documents.append(
                pdf_path.name
            )

            register_document(
                filename=pdf_path.name,
                chunk_count=len(document_chunks),
                vector_count=len(document_chunks)
            )

        except Exception as error:

            print(
                f"Could not load "
                f"{pdf_path.name}: {error}"
            )

    # Build combined FAISS index

    if chunks:

        rebuild_faiss_index()

    print(
        f"Knowledge base ready."
    )

    print(
        f"Documents: {len(documents)}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )


# ============================================================
# 16. INITIALIZE KNOWLEDGE BASE
# ============================================================

print(
    "Initializing RAG-Assist knowledge base..."
)

load_existing_documents()

# If there are no documents, make sure
# the default document is available.

if not documents:

    if DEFAULT_PDF_PATH.exists():

        load_document(
            DEFAULT_PDF_PATH,
            "AI_ML_Sample_Document.pdf"
        )

    else:

        print(
            "WARNING: Default AI/ML PDF "
            "was not found."
        )


# ============================================================
# 17. SEARCH DOCUMENTS
# ============================================================

def search_documents(
    question,
    top_k=3
):
    """
    Search across ALL documents using FAISS.
    """

    if index is None:

        raise RuntimeError(
            "No documents have been loaded."
        )

    if not chunks:

        raise RuntimeError(
            "Knowledge base contains "
            "no searchable chunks."
        )

    # Never request more results
    # than available vectors

    top_k = min(
        top_k,
        index.ntotal
    )

    question_embedding = (
        embedding_model.encode(
            [question],
            convert_to_numpy=True
        ).astype("float32")
    )

    distances, indices = index.search(
        question_embedding,
        top_k
    )

    results = []

    for position, chunk_index in enumerate(
        indices[0]
    ):

        if (
            chunk_index != -1
            and chunk_index < len(chunks)
        ):

            results.append(
                {
                    "text": chunks[chunk_index],
                    "source": chunk_sources[chunk_index],
                    "distance": float(
                        distances[0][position]
                    ),
                }
            )

    return results


def call_gemini_with_fallback(prompt):
    """
    Generate content using Gemini API with automatic retries and exponential backoff
    to handle free tier rate limits (429) gracefully.
    """
    import time

    models = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-flash-latest"]
    max_retries = 3

    for model_name in models:
        for attempt in range(max_retries):
            try:
                response = get_client().models.generate_content_stream(
                    model=model_name,
                    contents=prompt
                )
                if response:
                    return response
            except Exception as error:
                error_str = str(error).lower()
                # If rate limited (429), sleep for 6 seconds and retry automatically
                if "429" in error_str or "resource_exhausted" in error_str:
                    if attempt < max_retries - 1:
                        time.sleep(6)
                        continue
                # If model not found (404), break to next model in list
                if "404" in error_str or "not_found" in error_str:
                    break
                # For final attempt or other errors, continue to next model
                if attempt == max_retries - 1:
                    break

    return (
        "⚠️ Gemini API free tier rate limit reached. "
        "Please wait about 10–15 seconds and ask your question again."
    )



# ============================================================
# 18. GENERATE ANSWER USING GEMINI
# ============================================================

def generate_answer(question):
    """
    Answer a question using the RAG knowledge base when
    documents are available.

    If no documents are available, fall back to general
    AI/ML-focused Gemini answering.
    """

    # --------------------------------------------------------
    # GENERAL AI MODE
    # --------------------------------------------------------

    if not chunks or index is None:
        prompt = f"""
You are Mini-RAG, an AI assistant focused on
Artificial Intelligence and Machine Learning.

There are currently no uploaded documents in the
knowledge base.

Answer the user's question using your general
knowledge about Artificial Intelligence and
Machine Learning.

Do not pretend that the answer came from a document.
Keep the answer clear, useful, and concise.

USER QUESTION:
{question}

Provide a helpful answer.
"""

        return call_gemini_with_fallback(prompt)

    # --------------------------------------------------------
    # RAG MODE
    # --------------------------------------------------------

    search_results = search_documents(
        question,
        top_k=5
    )

    context_parts = []

    for result in search_results:
        context_parts.append(
            f"""
SOURCE DOCUMENT:
{result["source"]}

CONTENT:
{result["text"]}
"""
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
You are Mini-RAG, an AI assistant focused on
Artificial Intelligence and Machine Learning.

You have access to a persistent knowledge base
containing the built-in AI/ML document and documents
uploaded by users.

Answer the user's question using the most relevant
information from the provided knowledge base.

IMPORTANT RULES:

1. Prefer information directly relevant to the question.

2. If an uploaded document contains relevant
   information, use it.

3. Do not claim information came from a document
   unless it is actually present in the context.

4. Do not invent document-specific information.

5. If the exact answer cannot be found in the
   provided context, say that the information could
   not be found in the current knowledge base.

6. Keep the answer clear and concise.

KNOWLEDGE BASE CONTEXT
======================

{context}

USER QUESTION
=============

{question}

Provide a helpful answer.
"""

    return call_gemini_with_fallback(prompt)



# ============================================================
# 19. GET CURRENT KNOWLEDGE BASE INFORMATION
# ============================================================

def get_document_info():
    """
    Return information about the complete
    knowledge base.
    """

    return {
        "documents": documents,
        "document_count": len(documents),
        "total_chunks": len(chunks),
        "total_vectors": (
            index.ntotal
            if index
            else 0
        ),
    }


# ============================================================
# 20. GET DOCUMENT LIST
# ============================================================

def get_document_names():
    """
    Return names of all documents
    currently in the knowledge base.
    """

    return list(
        documents
    )