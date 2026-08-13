# RAG-Assist

Copyright © 2026 Azhar Khan

AI-powered document knowledge assistant using Retrieval-Augmented Generation (RAG), FAISS, Sentence Transformers, and Google Gemini.

## 🚀 Overview

RAG-Assist allows users to upload documents and ask questions about their content using natural language.

Instead of sending the entire document to an AI model, RAG-Assist:
1. Extracts text from documents
2. Splits the text into smaller chunks
3. Converts chunks into vector embeddings
4. Stores embeddings in FAISS
5. Retrieves the most relevant chunks for a question
6. Sends the retrieved context to Google Gemini
7. Generates a context-aware answer

This makes the system more efficient and helps keep answers grounded in the uploaded documents.

## ✨ Features

- 📄 Upload PDF, DOCX, and TXT documents
- 🔍 Semantic document retrieval
- 🧠 Sentence Transformer embeddings
- ⚡ FAISS vector search
- 🤖 Google Gemini-powered answer generation
- 💬 Natural-language document Q&A
- 📚 Multiple-document knowledge base
- 🌐 Streamlit web interface
- 🚀 FastAPI backend
- 🔐 Environment-based API key configuration

## 🏗️ RAG Workflow

```text
Document Upload
      ↓
Text Extraction
      ↓
Text Chunking
      ↓
Generate Embeddings
      ↓
FAISS Vector Database
      ↓
User Question
      ↓
Semantic Retrieval
      ↓
Relevant Context
      ↓
Google Gemini
      ↓
AI-Generated Answer