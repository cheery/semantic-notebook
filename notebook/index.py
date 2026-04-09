from __future__ import annotations

import threading
import chromadb

from notebook.config import CHROMADB_DIR, COLLECTION_NAME
from notebook.store import Note
from notebook.embeddings import embed_text, embed_batch

_client: chromadb.PersistentClient | None = None
_lock = threading.Lock()


def get_client() -> chromadb.PersistentClient:
    global _client
    with _lock:
        if _client is None:
            CHROMADB_DIR.mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
        return _client


def get_collection() -> chromadb.Collection:
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def note_id(note: Note) -> str:
    return note.rel_path


def index_note(note: Note) -> None:
    coll = get_collection()
    embedding = embed_text(note.content)
    coll.upsert(
        ids=[note_id(note)],
        embeddings=[embedding],
        documents=[note.content],
        metadatas=[{"title": note.title, "path": str(note.path), "mtime": note.mtime}],
    )


def remove_note(note_path: str) -> None:
    coll = get_collection()
    try:
        coll.delete(ids=[note_path])
    except Exception:
        pass


def sync_index(notes: list[Note], on_progress=None) -> dict:
    coll = get_collection()
    existing = {}
    try:
        result = coll.get(include=["metadatas"])
        for id_, meta in zip(result["ids"], result["metadatas"]):
            existing[id_] = meta.get("mtime", 0)
    except Exception:
        pass

    to_index = []
    current_ids = set()
    for note in notes:
        nid = note_id(note)
        current_ids.add(nid)
        stored_mtime = existing.get(nid, 0)
        if note.mtime > stored_mtime:
            to_index.append(note)

    to_remove = set(existing.keys()) - current_ids

    # Batch index new/changed notes
    if to_index:
        texts = [n.content for n in to_index]
        embeddings = embed_batch(texts)
        ids = [note_id(n) for n in to_index]
        metadatas = [{"title": n.title, "path": str(n.path), "mtime": n.mtime} for n in to_index]
        coll.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    # Remove deleted notes
    if to_remove:
        coll.delete(ids=list(to_remove))

    return {"indexed": len(to_index), "removed": len(to_remove), "unchanged": len(notes) - len(to_index)}


def query(embedding: list[float], n: int = 10) -> list[dict]:
    coll = get_collection()
    count = coll.count()
    if count == 0:
        return []
    results = coll.query(query_embeddings=[embedding], n_results=min(n, count))
    out = []
    for i in range(len(results["ids"][0])):
        out.append({
            "id": results["ids"][0][i],
            "distance": results["distances"][0][i],
            "metadata": results["metadatas"][0][i],
            "document": results["documents"][0][i] if results["documents"] else "",
        })
    return out


def get_all_embeddings() -> tuple[list[str], list[list[float]], list[dict]]:
    coll = get_collection()
    count = coll.count()
    if count == 0:
        return [], [], []
    result = coll.get(include=["embeddings", "metadatas"])
    return result["ids"], result["embeddings"], result["metadatas"]
