import os
import time
from core.logger import log_event
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "hr_docs")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)

embedding_model = SentenceTransformer(EMBEDDING_MODEL)
MIN_SCORE = 0.50
LIMIT = 5

def vector_agent(task_input: str, request_id: str):
    start_time = time.time()

    log_event("AGENT_STARTED", {
        "request_id": request_id,
        "agent": "VECTOR_AGENT",
        "input": task_input
    })

    try:
        query_vector = embedding_model.encode(
            task_input,
            convert_to_numpy=True
        ).tolist()

        search_result = client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            limit=LIMIT,
            score_threshold=MIN_SCORE
        )

        duration_ms = round((time.time() - start_time) * 1000, 2)
        top_score = search_result.points[0].score if search_result else None

        log_event("VECTOR_SEARCH_COMPLETED", {
            "request_id": request_id,
            "limit": LIMIT,
            "score_threshold": MIN_SCORE,
            "matched_chunks": len(search_result.points),
            "top_score": top_score,
            "duration_ms": duration_ms
        })

        chunks = []

        for item in search_result.points:
            payload = item.payload or {}

            chunks.append({
                "score": item.score,
                "text": payload.get("text", ""),
                "source": payload.get("source", ""),
                "title": payload.get("title", "")
            })

        if not chunks:
            return {
                "message": "No matching vector result found.",
                "chunks": []
            }

        retrieved_context = "\n\n".join(
            chunk["text"] for chunk in chunks
        )

        log_event("AGENT_COMPLETED", {
            "request_id": request_id,
            "agent": "VECTOR_AGENT",
            "success": True,
            "duration_ms": duration_ms
        })

        return {
            "query": task_input,
            "chunks": chunks,
            "retrieved_context": retrieved_context
        }

    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)

        log_event("AGENT_FAILED", {
            "request_id": request_id,
            "agent": "VECTOR_AGENT",
            "error": str(e),
            "duration_ms": duration_ms
        })

        return {
            "error": str(e)
        }