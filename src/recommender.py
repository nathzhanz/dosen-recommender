"""Profil dosen sebagai dokumen, ranking dosen, penjelasan, dan pertimbangan beban bimbingan."""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .expand import perluas
from .index import InvertedIndex
from .preprocess import preprocess
from .ranking import MODELS, bm25_scores, rank

DATA = Path(__file__).resolve().parent.parent / "data"


def using_sample_data(data_dir: Path = DATA) -> bool:
    return not (data_dir / "theses.csv").exists()


def load_data(data_dir: Path = DATA):
    """Pakai data asli di data/ bila ada; kalau tidak, jatuh ke data contoh sintetis di data/sample/."""
    if using_sample_data(data_dir):
        data_dir = data_dir / "sample"
    lecturers = pd.read_csv(data_dir / "lecturers.csv")
    pubs = pd.read_csv(data_dir / "publications.csv")
    theses = pd.read_csv(data_dir / "theses.csv")
    return lecturers, pubs, theses


@dataclass
class Recommender:
    lecturers: pd.DataFrame
    pubs: pd.DataFrame
    theses: pd.DataFrame
    profile: str = "gabungan"  # "publikasi", "gabungan" (publikasi + skripsi), atau "gabungan+keahlian"
    bobot_keahlian: int = 1    # berapa kali teks keahlian dosen diulang di profil "gabungan+keahlian"

    def __post_init__(self):
        self.lec_ids = list(self.lecturers["id"])
        self._items = {}  # lecturer_id -> [(sumber, judul)]
        for lid in self.lec_ids:
            items = [("publikasi", t) for t in self.pubs.loc[self.pubs.lecturer_id == lid, "judul"]]
            if self.profile in ("gabungan", "gabungan+keahlian"):
                items += [("skripsi", t) for t in self.theses.loc[self.theses.lecturer_id == lid, "judul"]]
            if self.profile == "gabungan+keahlian":
                row = self.lecturers.loc[self.lecturers.id == lid].iloc[0]
                keahlian = ", ".join(str(row.get(c, "")) for c in ("pakar", "rumpun_kbi") if str(row.get(c, "")) not in ("", "nan"))
                if keahlian:
                    items += [("keahlian", keahlian)] * self.bobot_keahlian
            self._items[lid] = items
        texts = {i: " . ".join(t for _, t in self._items[lid]) for i, lid in enumerate(self.lec_ids)}
        self.index = InvertedIndex.build(texts)
        self.load = self.theses.groupby("lecturer_id").size().to_dict()

    def recommend(self, query: str, model: str = "BM25", k: int = 3, load_weight: float = 0.0,
                  expand: bool = False):
        """Ranking dosen. load_weight>0 menurunkan skor dosen yang kuotanya hampir penuh.
        expand=True menambahkan sinonim Indonesia-Inggris ke query (src/expand.py)."""
        if expand:
            query = perluas(query)[0]
        scores = MODELS[model](self.index, query)
        if load_weight > 0:
            quota = dict(zip(self.lecturers["id"], self.lecturers["kuota"]))
            for d in list(scores):
                lid = self.lec_ids[d]
                ratio = min(self.load.get(lid, 0) / max(quota[lid], 1), 1.5)
                scores[d] *= 1 - load_weight * min(ratio, 1.0)
        results = []
        for d, s in rank(scores, k):
            lid = self.lec_ids[d]
            row = self.lecturers.loc[self.lecturers.id == lid].iloc[0]
            results.append({"id": lid, "nama": row["nama"], "bidang": row["bidang"], "skor": s,
                            "rumpun": str(row.get("rumpun_kbi", "") or ""), "pakar": str(row.get("pakar", "") or ""),
                            "beban": f"{self.load.get(lid, 0)}/{row['kuota']}"})
        return results

    def explain(self, query: str, lecturer_id: str, top_items: int = 3, top_terms: int = 5,
                expand: bool = False):
        """Kata kunci dan judul (publikasi/skripsi) yang membuat dosen dianggap cocok."""
        if expand:
            query = perluas(query)[0]
        d = self.lec_ids.index(lecturer_id)
        _, contrib = bm25_scores(self.index, query, return_terms=True)
        term_scores = sorted(contrib.get(d, {}).items(), key=lambda x: -x[1])[:top_terms]
        q_terms = set(preprocess(query))
        scored = []
        for source, title in self._items[lecturer_id]:
            overlap = q_terms & set(preprocess(title))
            if overlap:
                scored.append((len(overlap), source, title, sorted(overlap)))
        scored.sort(key=lambda x: -x[0])
        return {"kata_kunci": [t for t, _ in term_scores],
                "judul_pendukung": [{"sumber": s, "judul": t, "term_cocok": o} for _, s, t, o in scored[:top_items]]}
