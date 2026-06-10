import os
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

def vector_agent(task_input: str):
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

        return {
            "query": task_input,
            "chunks": chunks
        }

    except Exception as e:
        return {
            "error": str(e)
        }