"""Inverted index yang dibangun sendiri (tanpa library mesin pencari)."""
import math
from collections import Counter, defaultdict

from .preprocess import preprocess


class InvertedIndex:
    def __init__(self):
        self.postings: dict[str, dict[int, int]] = defaultdict(dict)  # term -> {doc_id: tf}
        self.doc_len: dict[int, int] = {}
        self.doc_ids: list[int] = []
        self.N = 0
        self.avgdl = 0.0

    def add_document(self, doc_id: int, text: str) -> None:
        terms = preprocess(text)
        for term, tf in Counter(terms).items():
            self.postings[term][doc_id] = tf
        self.doc_len[doc_id] = len(terms)
        self.doc_ids.append(doc_id)

    def finalize(self) -> None:
        self.N = len(self.doc_ids)
        self.avgdl = sum(self.doc_len.values()) / max(self.N, 1)
        # norma vektor TF-IDF per dokumen (untuk cosine)
        sq = defaultdict(float)
        for term, plist in self.postings.items():
            idf = self.idf(term)
            for d, tf in plist.items():
                sq[d] += ((1 + math.log(tf)) * idf) ** 2
        self.doc_norm = {d: math.sqrt(v) or 1.0 for d, v in sq.items()}

    def df(self, term: str) -> int:
        return len(self.postings.get(term, ()))

    def idf(self, term: str) -> float:
        """IDF smooth untuk TF-IDF."""
        return math.log((1 + self.N) / (1 + self.df(term))) + 1

    def bm25_idf(self, term: str) -> float:
        n = self.df(term)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    @classmethod
    def build(cls, texts: dict[int, str]) -> "InvertedIndex":
        idx = cls()
        for d, t in texts.items():
            idx.add_document(d, t)
        idx.finalize()
        return idx
