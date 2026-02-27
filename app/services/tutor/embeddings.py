"""pgvector embeddings and RAG (Retrieval-Augmented Generation) service.

Provides text chunking, embedding generation, storage in pgvector,
and context retrieval for course-aware tutoring.
"""

import hashlib
import json
import logging
from typing import Any

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Embedding dimensions (placeholder — will match the embedding model used)
EMBEDDING_DIM = 1536


def chunk_text(
    content: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks for embedding.

    Args:
        content: The full text to chunk.
        chunk_size: Target number of characters per chunk.
        overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if not content or not content.strip():
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(content)

    while start < text_length:
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < text_length:
            # Look for the last period, question mark, or newline within the chunk
            for sep in [". ", "? ", "! ", "\n\n", "\n"]:
                last_sep = content.rfind(sep, start + chunk_size // 2, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break

        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward, accounting for overlap
        start = end - overlap if end < text_length else text_length

    return chunks


async def generate_embeddings(
    chunks: list[str],
    user_id: int,
    course_id: int | None,
    material_id: int | None,
    session: AsyncSession,
) -> int:
    """Generate embeddings for text chunks and store them in pgvector.

    This is a stub that generates deterministic placeholder embeddings.
    In production, replace _compute_embedding with a real embedding API call
    (e.g. OpenAI text-embedding-3-small, Cohere embed, or a local model).

    Args:
        chunks: List of text strings to embed.
        user_id: Owner of the material.
        course_id: Associated course (for scoped retrieval).
        material_id: Source material ID.
        session: Database session.

    Returns:
        Number of chunks stored.
    """
    stored = 0

    for i, chunk in enumerate(chunks):
        embedding = _compute_embedding(chunk)
        chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()[:16]

        try:
            await session.execute(
                text("""
                    INSERT INTO embeddings (
                        user_id, course_id, material_id,
                        chunk_index, chunk_text, chunk_hash,
                        embedding
                    )
                    VALUES (
                        :user_id, :course_id, :material_id,
                        :chunk_index, :chunk_text, :chunk_hash,
                        :embedding
                    )
                    ON CONFLICT (chunk_hash) DO UPDATE SET
                        chunk_text = EXCLUDED.chunk_text,
                        embedding = EXCLUDED.embedding
                """),
                {
                    "user_id": user_id,
                    "course_id": course_id,
                    "material_id": material_id,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "chunk_hash": chunk_hash,
                    "embedding": json.dumps(embedding),
                },
            )
            stored += 1
        except Exception as exc:
            logger.error("Failed to store embedding for chunk %d: %s", i, exc)

    await session.commit()
    logger.info("Stored %d/%d embeddings for user %d", stored, len(chunks), user_id)
    return stored


async def retrieve_context(
    query: str,
    user_id: int,
    course_id: int | None = None,
    top_k: int = 5,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """Retrieve the most relevant chunks for a query using vector similarity.

    Args:
        query: The user's question or search text.
        user_id: Restrict to this user's materials.
        course_id: Optional course filter for scoped retrieval.
        top_k: Number of top results to return.
        session: Database session.

    Returns:
        List of dicts with 'chunk_text', 'score', 'material_id', 'course_id'.
    """
    if session is None:
        logger.warning("No database session provided for retrieval.")
        return []

    query_embedding = _compute_embedding(query)

    # Build the SQL query with optional course filter
    course_filter = "AND course_id = :course_id" if course_id else ""

    try:
        result = await session.execute(
            text(f"""
                SELECT
                    chunk_text,
                    material_id,
                    course_id,
                    1 - (embedding <=> :query_embedding::vector) AS score
                FROM embeddings
                WHERE user_id = :user_id
                {course_filter}
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :top_k
            """),
            {
                "query_embedding": json.dumps(query_embedding),
                "user_id": user_id,
                "course_id": course_id,
                "top_k": top_k,
            },
        )
        rows = result.fetchall()

        return [
            {
                "chunk_text": row.chunk_text,
                "score": round(float(row.score), 4),
                "material_id": row.material_id,
                "course_id": row.course_id,
            }
            for row in rows
        ]
    except Exception as exc:
        logger.error("Embedding retrieval failed: %s", exc)
        return []


def _compute_embedding(text_input: str) -> list[float]:
    """Compute an embedding vector for the given text.

    STUB: Returns a deterministic placeholder vector based on text hash.
    Replace with a real embedding API call in production, e.g.:

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        # Or use OpenAI / Cohere / local model for embeddings

    Args:
        text_input: Text to embed.

    Returns:
        List of floats representing the embedding vector.
    """
    # Deterministic placeholder: hash-based pseudo-embedding
    hash_bytes = hashlib.sha512(text_input.encode()).digest()
    # Expand to EMBEDDING_DIM floats in [-1, 1]
    embedding: list[float] = []
    for i in range(EMBEDDING_DIM):
        byte_val = hash_bytes[i % len(hash_bytes)]
        embedding.append((byte_val / 127.5) - 1.0)
    return embedding
