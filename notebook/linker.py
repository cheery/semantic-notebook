from notebook.index import query, get_collection
from notebook.embeddings import embed_text


def find_related(note_id: str, n: int = 5) -> list[dict]:
    coll = get_collection()
    try:
        result = coll.get(ids=[note_id], include=["embeddings"])
        if not result["ids"]:
            return []
        embedding = result["embeddings"][0]
    except Exception:
        return []

    # Query n+1 to account for self
    results = query(embedding, n=n + 1)
    related = [r for r in results if r["id"] != note_id][:n]
    for r in related:
        r["score"] = max(0.0, 1.0 - r["distance"])
    return related
