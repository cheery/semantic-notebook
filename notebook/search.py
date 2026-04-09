from notebook.embeddings import embed_text
from notebook.index import query


def search(query_text: str, n: int = 10) -> list[dict]:
    embedding = embed_text(query_text)
    results = query(embedding, n=n)
    for r in results:
        r["score"] = max(0.0, 1.0 - r["distance"])
        # Extract snippet — first non-heading, non-empty line
        lines = r.get("document", "").splitlines()
        snippet = ""
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                snippet = stripped[:120]
                break
        r["snippet"] = snippet
    return results
