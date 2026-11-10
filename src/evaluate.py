"""Evaluasi hold-out: judul skripsi lama dijadikan query, cek apakah pembimbing asli di top-k.

Skripsi uji DIKELUARKAN dari profil dosen (tidak bocor). Metrik: Success@1, Success@3, MRR.
Menjalankan: python -m src.evaluate
"""
import json
import random
from pathlib import Path

import pandas as pd

from .recommender import Recommender, load_data

OUT = Path(__file__).resolve().parent.parent / "eval"
N_QUERY = 30
SEED = 7


def split_queries(theses: pd.DataFrame, n: int = N_QUERY, seed: int = SEED):
    rng = random.Random(seed)
    # ambil query secara merata antar dosen agar tidak bias
    by_lec = {lid: list(g.index) for lid, g in theses.groupby("lecturer_id")}
    picks = []
    while len(picks) < n:
        for lid, idxs in by_lec.items():
            if idxs and len(picks) < n:
                picks.append(idxs.pop(rng.randrange(len(idxs))))
    return theses.loc[picks]


def metrics(ranked_ids: list[list[str]], truth: list[str]):
    s1 = s3 = rr = 0.0
    for ranked, t in zip(ranked_ids, truth):
        if t in ranked:
            pos = ranked.index(t) + 1
            rr += 1 / pos
            s1 += pos <= 1
            s3 += pos <= 3
    n = len(truth)
    return {"Success@1": s1 / n, "Success@3": s3 / n, "MRR": rr / n}


def run():
    lecturers, pubs, theses = load_data()
    test = split_queries(theses)
    train = theses.drop(test.index)
    rows, details = [], []
    configs = [(p, m) for p in ("publikasi", "gabungan") for m in ("TF-IDF", "BM25")]
    for profile, model in configs:
        rec = Recommender(lecturers, pubs, train, profile=profile)
        ranked, truth = [], []
        for _, r in test.iterrows():
            res = rec.recommend(r["judul"], model=model, k=len(lecturers))
            ranked.append([x["id"] for x in res]); truth.append(r["lecturer_id"])
            if profile == "gabungan":
                top = ranked[-1][0] if ranked[-1] else None
                details.append({"model": model, "query": r["judul"], "benar": r["lecturer_id"],
                                "top3": ranked[-1][:3], "gagal_top3": r["lecturer_id"] not in ranked[-1][:3]})
        rows.append({"profil": profile, "model": model, **metrics(ranked, truth)})
    OUT.mkdir(exist_ok=True)
    df = pd.DataFrame(rows).round(3)
    df.to_csv(OUT / "hasil_evaluasi.csv", index=False)
    test[["thesis_id", "judul", "lecturer_id"]].to_csv(OUT / "query_uji.csv", index=False)
    (OUT / "query_gagal.json").write_text(
        json.dumps([d for d in details if d["gagal_top3"]], indent=2, ensure_ascii=False), encoding="utf-8")
    print(df.to_string(index=False))
    return df


if __name__ == "__main__":
    run()
