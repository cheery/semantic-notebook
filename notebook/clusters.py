from dataclasses import dataclass
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

from notebook.config import MAX_CLUSTERS
from notebook.index import get_all_embeddings


@dataclass
class Cluster:
    label: str
    note_ids: list[str]
    note_titles: list[str]


def _pick_k(embeddings: np.ndarray, max_k: int) -> int:
    n = len(embeddings)
    if n <= 3:
        return min(n, 2)
    best_k, best_score = 2, -1
    for k in range(2, min(max_k + 1, n)):
        km = KMeans(n_clusters=k, n_init=5, random_state=42)
        labels = km.fit_predict(embeddings)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(embeddings, labels, sample_size=min(300, n))
        if score > best_score:
            best_k, best_score = k, score
    return best_k


def _cluster_label(documents: list[str], top_n: int = 3) -> str:
    if not documents:
        return "misc"
    try:
        tfidf = TfidfVectorizer(stop_words="english", max_features=100)
        matrix = tfidf.fit_transform(documents)
        scores = np.asarray(matrix.sum(axis=0)).flatten()
        top_idx = scores.argsort()[-top_n:][::-1]
        words = tfidf.get_feature_names_out()
        return " / ".join(words[i] for i in top_idx)
    except Exception:
        return "misc"


def get_clusters() -> list[Cluster]:
    ids, embeddings, metadatas = get_all_embeddings()
    if len(ids) < 2:
        if ids:
            return [Cluster(label="all", note_ids=ids, note_titles=[m.get("title", "") for m in metadatas])]
        return []

    emb_array = np.array(embeddings)
    k = _pick_k(emb_array, MAX_CLUSTERS)
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(emb_array)

    # Group notes by cluster
    from notebook.index import get_collection
    coll = get_collection()
    all_docs = coll.get(ids=ids, include=["documents"])
    doc_map = dict(zip(all_docs["ids"], all_docs["documents"]))

    clusters_map: dict[int, list[tuple[str, str, str]]] = {}
    for i, label in enumerate(labels):
        entry = (ids[i], metadatas[i].get("title", ""), doc_map.get(ids[i], ""))
        clusters_map.setdefault(label, []).append(entry)

    result = []
    for cluster_id in sorted(clusters_map):
        entries = clusters_map[cluster_id]
        docs = [e[2] for e in entries]
        label = _cluster_label(docs)
        result.append(Cluster(
            label=label,
            note_ids=[e[0] for e in entries],
            note_titles=[e[1] for e in entries],
        ))
    return result
