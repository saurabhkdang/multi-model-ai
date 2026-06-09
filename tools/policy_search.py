from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from llm_client import call_llm


POLICY_FILE = Path("data/policies.txt")

model = SentenceTransformer("all-MiniLM-L6-v2")

chunks = []
chunk_embeddings = None
last_modified = None


def read_policy_file():
    if not POLICY_FILE.exists():
        return ""

    return POLICY_FILE.read_text(encoding="utf-8")


def load_policy_chunks():
    global chunks, chunk_embeddings

    data = read_policy_file()

    if not data:
        chunks = []
        chunk_embeddings = None
        return

    chunks = [
        section.strip()
        for section in data.split("------------------------------------------------")
        if section.strip()
    ]

    chunk_embeddings = model.encode(
        chunks,
        convert_to_numpy=True
    )


def cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


def policy_search_tool(query: str):
    global chunks, chunk_embeddings, last_modified

    current_modified = os.path.getmtime(
        POLICY_FILE
    )

    if (
        chunk_embeddings is None
        or last_modified != current_modified
    ):
        load_policy_chunks()
        last_modified = current_modified

    if not chunks:
        return "Policy file not found or empty."

    query_embedding = model.encode(
        query,
        convert_to_numpy=True
    )

    scores = []

    for index, chunk_embedding in enumerate(chunk_embeddings):
        score = cosine_similarity(query_embedding, chunk_embedding)

        scores.append({
            "chunk": chunks[index],
            "score": float(score)
        })

    scores = sorted(
        scores,
        key=lambda item: item["score"],
        reverse=True
    )

    best_matches = scores[:2]

    context  = "\n\n".join(
        match["chunk"]
        for match in best_matches
    )

    prompt = f"""
    You are an HR assistant.

    Answer ONLY using the provided context.

    If answer is not present in context,
    say:

    "I could not find this information."

    Context:

    {context}

    Question:

    {query}

    Answer:
    """

    answer = call_llm(prompt)

    return answer