"""Dua model ranking di atas inverted index: TF-IDF (cosine) dan BM25."""
import math
from collections import Counter, defaultdict

from .index import InvertedIndex
from .preprocess import preprocess


def tfidf_scores(index: InvertedIndex, query: str) -> dict[int, float]:
    q_terms = Counter(preprocess(query))
    q_w = {t: (1 + math.log(c)) * index.idf(t) for t, c in q_terms.items() if t in index.postings}
    q_norm = math.sqrt(sum(w * w for w in q_w.values())) or 1.0
    scores = defaultdict(float)
    for t, qw in q_w.items():
        idf = index.idf(t)
        for d, tf in index.postings[t].items():
            scores[d] += qw * (1 + math.log(tf)) * idf
    return {d: s / (q_norm * index.doc_norm[d]) for d, s in scores.items()}


def bm25_scores(index: InvertedIndex, query: str, k1: float = 1.5, b: float = 0.75,
                return_terms: bool = False):
    q_terms = set(preprocess(query))
    scores = defaultdict(float)
    contrib = defaultdict(lambda: defaultdict(float))  # doc -> term -> skor (untuk penjelasan)
    for t in q_terms:
        if t not in index.postings:
            continue
        idf = index.bm25_idf(t)
        for d, tf in index.postings[t].items():
            norm = tf + k1 * (1 - b + b * index.doc_len[d] / index.avgdl)
            s = idf * tf * (k1 + 1) / norm
            scores[d] += s
            contrib[d][t] = s
    return (dict(scores), contrib) if return_terms else dict(scores)


MODELS = {"TF-IDF": tfidf_scores, "BM25": bm25_scores}


def rank(scores: dict[int, float], k: int | None = None) -> list[tuple[int, float]]:
    ordered = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return ordered[:k] if k else ordered
