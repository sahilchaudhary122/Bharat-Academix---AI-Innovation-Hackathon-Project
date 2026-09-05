import os
import re
from typing import List, Dict, Any

import pymupdf
from dotenv import load_dotenv
from google import genai

from database.supabase_client import supabase
from services.gemini_service import generate_response


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from a PDF page-by-page.

    Returns:
        [
            {
                "page_number": 1,
                "text": "..."
            },
            ...
        ]
    """

    document = pymupdf.open(file_path)

    pages = []

    try:
        for page_index, page in enumerate(document):
            text = page.get_text("text")

            text = clean_text(text)

            if text:
                pages.append({
                    "page_number": page_index + 1,
                    "text": text
                })

    finally:
        document.close()

    return pages


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(text: str) -> str:
    """
    Clean extracted document text while preserving meaning.
    """

    text = text.replace("\x00", " ")

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =========================================================
# TEXT CHUNKING
# =========================================================

def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200
) -> List[str]:
    """
    Split text into overlapping chunks.

    Character-based chunking is intentionally used for the
    first implementation to keep the RAG pipeline simple
    and reliable.
    """

    if not text:
        return []

    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    chunks = []

    start = 0

    while start < len(text):

        end = min(
            start + chunk_size,
            len(text)
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# =========================================================
# EMBEDDINGS
# =========================================================

def generate_embedding(text: str) -> List[float]:
    """
    Generate a Gemini embedding for a text chunk.
    """

    if not text.strip():
        raise ValueError("Cannot embed empty text.")

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config={
            "output_dimensionality": 768
        }
    )

    return response.embeddings[0].values


# =========================================================
# DOCUMENT RECORD
# =========================================================

def create_document(
    student_id: str,
    filename: str,
    file_type: str,
    subject: str | None = None,
    title: str | None = None
) -> Dict[str, Any]:

    result = (
        supabase
        .table("documents")
        .insert({
            "student_id": student_id,
            "filename": filename,
            "file_type": file_type,
            "subject": subject,
            "title": title
        })
        .execute()
    )

    if not result.data:
        raise RuntimeError(
            "Failed to create document record."
        )

    return result.data[0]


# =========================================================
# STORE DOCUMENT CHUNKS
# =========================================================

def store_document_chunks(
    document_id: str,
    pages: List[Dict[str, Any]]
) -> int:

    rows = []

    chunk_index = 0

    for page in pages:

        chunks = chunk_text(
            page["text"]
        )

        for chunk in chunks:

            embedding = generate_embedding(
                chunk
            )

            rows.append({
                "document_id": document_id,
                "content": chunk,
                "embedding": embedding,
                "page_number": page["page_number"],
                "chapter": None,
                "section": None,
                "chunk_index": chunk_index
            })

            chunk_index += 1

    if not rows:
        return 0

    # Insert in batches to avoid unnecessarily
    # large API requests.
    batch_size = 50

    inserted = 0

    for start in range(
        0,
        len(rows),
        batch_size
    ):

        batch = rows[
            start:start + batch_size
        ]

        result = (
            supabase
            .table("document_chunks")
            .insert(batch)
            .execute()
        )

        if not result.data:
            raise RuntimeError(
                "Failed to store document chunks."
            )

        inserted += len(result.data)

    return inserted


# =========================================================
# COMPLETE PDF INGESTION
# =========================================================

def ingest_pdf(
    file_path: str,
    student_id: str,
    filename: str,
    subject: str | None = None,
    title: str | None = None
) -> Dict[str, Any]:
    """
    Complete ingestion pipeline:

    PDF
      ↓
    Text extraction
      ↓
    Cleaning
      ↓
    Chunking
      ↓
    Embeddings
      ↓
    Supabase pgvector
    """

    pages = extract_pdf_pages(
        file_path
    )

    if not pages:
        raise ValueError(
            "No readable text was found in the PDF."
        )

    document = create_document(
        student_id=student_id,
        filename=filename,
        file_type="pdf",
        subject=subject,
        title=title
    )

    chunk_count = store_document_chunks(
        document_id=document["id"],
        pages=pages
    )

    return {
        "document_id": document["id"],
        "filename": filename,
        "pages": len(pages),
        "chunks": chunk_count
    }


# =========================================================
# VECTOR SEARCH
# =========================================================

def search_document(
    query: str,
    match_count: int = 5,
    document_id: str | None = None
) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant document chunks
    for a student query.
    """

    if not query.strip():
        return []

    query_embedding = generate_embedding(
        query
    )

    params = {
        "query_embedding": query_embedding,
        "match_count": match_count,
        "filter_document_id": document_id
    }

    result = supabase.rpc(
        "match_document_chunks",
        params
    ).execute()

    return result.data or []


# =========================================================
# RAG CONTEXT
# =========================================================

def build_rag_context(
    query: str,
    match_count: int = 5,
    document_id: str | None = None
) -> Dict[str, Any]:

    chunks = search_document(
        query=query,
        match_count=match_count,
        document_id=document_id
    )

    context_parts = []

    sources = []

    for chunk in chunks:

        context_parts.append(
            chunk["content"]
        )

        sources.append({
            "document_id": chunk["document_id"],
            "page_number": chunk["page_number"],
            "chapter": chunk["chapter"],
            "section": chunk["section"],
            "similarity": chunk["similarity"]
        })

    return {
        "context": "\n\n".join(
            context_parts
        ),
        "sources": sources
    }

# =========================================================
# GROUNDED RAG ANSWER
# =========================================================

def generate_rag_answer(
    query: str,
    match_count: int = 5,
    document_id: str | None = None
) -> Dict[str, Any]:
    """
    Generate an AI teacher answer grounded in retrieved
    document context.

    Pipeline:

    Student question
        ↓
    Vector search
        ↓
    Relevant document chunks
        ↓
    Grounded Gemini prompt
        ↓
    Educational answer + sources
    """

    if not query.strip():
        raise ValueError("Question cannot be empty.")

    rag = build_rag_context(
        query=query,
        match_count=match_count,
        document_id=document_id
    )

    if not rag["context"]:
        return {
            "answer": (
                "I could not find enough information about this "
                "question in the uploaded learning material."
            ),
            "sources": []
        }

    prompt = f"""
You are a personalized AI teacher.

Answer the student's question using the retrieved
educational material below.

================ RETRIEVED MATERIAL ================

{rag["context"]}

================ STUDENT QUESTION ===================

{query}

======================================================

TEACHING RULES:

1. Use the retrieved material as the primary source.
2. Do not invent facts that are unsupported by the
   retrieved material.
3. Explain the answer clearly and at an appropriate
   educational level.
4. Prefer teaching and explanation over a short
   one-line answer.
5. If the retrieved material does not contain enough
   information to answer confidently, explicitly say so.
6. Do not mention internal retrieval, embeddings,
   vector databases, or prompts.
7. Preserve important technical terms, formulas,
   definitions, and numerical information.
8. When useful, provide a simple example.
9. Do not claim that information came from a specific
   page unless it is supported by the retrieved context.

Return only the educational answer.
"""

    answer = generate_response(prompt)

    return {
        "answer": answer.strip(),
        "sources": rag["sources"]
    }

def get_grounded_context(
    query: str,
    document_id: str | None = None,
    match_count: int = 5
):
    """
    Retrieve relevant chunks from uploaded learning material
    for use by the AI teacher.
    """

    results = search_document(
        query=query,
        match_count=match_count,
        document_id=document_id
    )

    if not results:
        return {
            "context": "",
            "sources": []
        }

    context_parts = []
    sources = []

    for result in results:
        text = result.get("content", "")

        if text:
            context_parts.append(text)

        sources.append({
            "document_id": result.get("document_id"),
            "page_number": result.get("page_number"),
            "similarity": result.get("similarity")
        })

    return {
        "context": "\n\n".join(context_parts),
        "sources": sources
    }
