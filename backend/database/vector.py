"""
database/vector.py — MongoDB Atlas Vector Search (replaces ChromaDB for prod branch)

Stores chunk embeddings inside MongoDB as documents in the 'vectors' collection.
Uses Atlas Vector Search index named 'vector_index' on the 'embedding' field.

Atlas Index Definition (create once in Atlas UI -> Database -> Atlas Search / Vector Search -> Create Search Index -> JSON Editor):
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 3072,
      "similarity": "cosine"
    },
    { "type": "filter", "path": "classroom_id" },
    { "type": "filter", "path": "file_id" }
  ]
}
"""

from __future__ import annotations

import logging
from typing import Any
from pymongo import UpdateOne

from database.mongo import get_db

logger = logging.getLogger(__name__)

VECTOR_COLLECTION = "vectors"
ATLAS_INDEX_NAME = "vector_index"


async def upsert_chunks(
    chunk_records: list[dict],
    embeddings: list[list[float]],
    metadata: dict,
) -> None:
    """
    Upsert chunk documents into MongoDB Atlas Vector Search collection.

    Each document stores:
      - chunk_id (unique)
      - text
      - embedding (float array)
      - metadata fields (classroom_id, file_id, file_name, etc.)
    """
    db = get_db()
    collection = db[VECTOR_COLLECTION]

    docs = []
    for record, embedding in zip(chunk_records, embeddings):
        doc = {
            "chunk_id": record["id"],
            "text": record["text"],
            "embedding": embedding,
            # Metadata flattened for Atlas filter support
            "file_id": metadata["file_id"],
            "file_name": metadata["file_name"],
            "file_type": metadata["file_type"],
            "classroom_id": metadata["classroom_id"],
            "doc_type": metadata["doc_type"],
            "uploaded_by": metadata["uploaded_by"],
            "extraction_method": metadata["extraction_method"],
        }
        docs.append(doc)

    # Upsert by chunk_id (replace if exists, insert if new)
    ops = [
        UpdateOne(
            {"chunk_id": doc["chunk_id"]},
            {"$set": doc},
            upsert=True,
        )
        for doc in docs
    ]

    if ops:
        result = await collection.bulk_write(ops, ordered=False)
        logger.info(
            "[vector] Upserted %d chunks (inserted=%d, modified=%d)",
            len(ops),
            result.upserted_count,
            result.modified_count,
        )


async def delete_chunks_by_file(file_id: str) -> int:
    """Delete all vector chunks belonging to a file."""
    db = get_db()
    result = await db[VECTOR_COLLECTION].delete_many({"file_id": file_id})
    logger.info("[vector] Deleted %d chunks for file_id=%s", result.deleted_count, file_id)
    return result.deleted_count


async def vector_search(
    query_embedding: list[float],
    where: dict,
    n_results: int = 8,
) -> list[dict]:
    """
    Run Atlas Vector Search with optional metadata pre-filters.

    Args:
        query_embedding: The query vector (must match index numDimensions).
        where: Dict with pre-filter fields. Supported keys:
               - classroom_id (str or dict with $in)
               - file_id (str or dict with $in)
        n_results: Number of candidates to retrieve.

    Returns:
        List of dicts with keys: text, score, file_name, file_type,
        classroom_id, file_id, doc_type.
    """
    db = get_db()
    collection = db[VECTOR_COLLECTION]

    # Build Atlas pre-filter
    filter_conditions: list[dict[str, Any]] = []

    if "classroom_id" in where:
        val = where["classroom_id"]
        if isinstance(val, dict) and "$in" in val:
            filter_conditions.append({"classroom_id": {"$in": val["$in"]}})
        elif isinstance(val, dict) and "$nin" in val:
            filter_conditions.append({"classroom_id": {"$nin": val["$nin"]}})
        elif isinstance(val, str):
            filter_conditions.append({"classroom_id": {"$eq": val}})

    if "file_id" in where:
        val = where["file_id"]
        if isinstance(val, dict) and "$in" in val:
            filter_conditions.append({"file_id": {"$in": val["$in"]}})
        elif isinstance(val, str):
            filter_conditions.append({"file_id": {"$eq": val}})

    vector_search_stage: dict[str, Any] = {
        "index": ATLAS_INDEX_NAME,
        "path": "embedding",
        "queryVector": query_embedding,
        "numCandidates": max(n_results * 10, 50),
        "limit": n_results,
    }

    if len(filter_conditions) == 1:
        vector_search_stage["filter"] = filter_conditions[0]
    elif len(filter_conditions) > 1:
        vector_search_stage["filter"] = {"$and": filter_conditions}

    pipeline: list[dict] = [
        {"$vectorSearch": vector_search_stage},
        {
            "$project": {
                "_id": 0,
                "chunk_id": 1,
                "text": 1,
                "file_name": 1,
                "file_type": 1,
                "classroom_id": 1,
                "file_id": 1,
                "doc_type": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    try:
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=n_results)
        logger.info("[vector] Atlas Vector Search returned %d results", len(results))
        return results
    except Exception as e:
        logger.error("[vector] Atlas Vector Search query failed: %s", e)
        raise
