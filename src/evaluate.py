"""Evaluasi hold-out: judul skripsi lama dijadikan query, cek apakah pembimbing asli di top-k.

- Satu skripsi bisa punya >1 pembimbing (beberapa baris dengan thesis_id sama). Query dianggap BENAR
  bila SALAH SATU pembimbing aslinya muncul (rank = posisi pembimbing asli yang paling atas).
- Semua baris skripsi uji (untuk semua pembimbingnya) DIKELUARKAN dari profil dosen, jadi tidak ada kebocoran.
Metrik: Success@1, Success@3, MRR.   Menjalankan: python -m src.evaluate
"""
import json
import random
from pathlib import Path

import pandas as pd

from .recommender import Recommender, load_data, using_sample_data

OUT = Path(__file__).resolve().parent.parent / "eval"
N_QUERY = 30
SEED = 7


def split_queries(theses: pd.DataFrame, n: int = N_QUERY, seed: int = SEED) -> pd.DataFrame:
    """Pilih n skripsi unik sebagai query, bergiliran antar dosen (pembimbing pertama) agar tidak bias."""
    rng = random.Random(seed)
    first = theses.drop_duplicates("thesis_id")  # satu baris per skripsi
    n = min(n, max(len(first) // 2, 1))  # jangan minta query lebih banyak dari data
    by_lec = {lid: list(g["thesis_id"]) for lid, g in first.groupby("lecturer_id")}
    picks = []
    while len(picks) < n:
        progressed = False
        for lid in list(by_lec):
            if by_lec[lid] and len(picks) < n:
                picks.append(by_lec[lid].pop(rng.randrange(len(by_lec[lid]))))
                progressed = True
        if not progressed:
            break
    return first[first["thesis_id"].isin(picks)]


def metrics(ranks: list[int | None]):
    n = len(ranks)
    s1 = sum(1 for r in ranks if r == 1)
    s3 = sum(1 for r in ranks if r is not None and r <= 3)
    mrr = sum(1 / r for r in ranks if r is not None)
    return {"Success@1": s1 / n, "Success@3": s3 / n, "MRR": mrr / n}


def run():
    if using_sample_data():
        print("PERINGATAN: memakai data sintetis; angka ini tidak boleh masuk laporan.")
    lecturers, pubs, theses = load_data()
    theses = theses.copy()
    theses["thesis_id"] = theses["thesis_id"].astype(str)
    manual = OUT / "query_uji_manual.csv"  # daftar query hasil kurasi manual (Naila); kalau ada, dipakai
    if manual.exists():
        ids = pd.read_csv(manual, dtype=str)["thesis_id"].tolist()
        first = theses.drop_duplicates("thesis_id")
        test = first[first["thesis_id"].isin(ids)]
        print(f"Memakai {len(test)} query dari {manual.name}")
    else:
        test = split_queries(theses)
    test_ids = set(test["thesis_id"])
    truth = theses[theses["thesis_id"].isin(test_ids)].groupby("thesis_id")["lecturer_id"].agg(set).to_dict()
    train = theses[~theses["thesis_id"].isin(test_ids)]
    rows, failures = [], []
    for profile in ("publikasi", "gabungan"):
        for model in ("TF-IDF", "BM25"):
            rec = Recommender(lecturers, pubs, train, profile=profile)
            ranks = []
            for _, r in test.iterrows():
                res = rec.recommend(r["judul"], model=model, k=len(lecturers))
                order = [x["id"] for x in res]
                pos = [order.index(l) + 1 for l in truth[r["thesis_id"]] if l in order]
                rank = min(pos) if pos else None
                ranks.append(rank)
                if profile == "gabungan" and (rank is None or rank > 3):
                    failures.append({"model": model, "query": r["judul"], "pembimbing_asli": sorted(truth[r["thesis_id"]]),
                                     "top3": order[:3], "rank_pembimbing_asli": rank})
            rows.append({"profil": profile, "model": model, **metrics(ranks)})
    OUT.mkdir(exist_ok=True)
    df = pd.DataFrame(rows).round(3)
    df.to_csv(OUT / "hasil_evaluasi.csv", index=False)
    if not manual.exists():  # jangan menimpa daftar manual
        test[["thesis_id", "judul"]].assign(pembimbing_asli=test["thesis_id"].map(lambda t: ",".join(sorted(truth[t])))) \
            .to_csv(OUT / "query_uji.csv", index=False)
    (OUT / "query_gagal.json").write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(test)} query uji, {len(train)} baris skripsi di profil, {len(lecturers)} dosen")
    print(df.to_string(index=False))
    return df


def run_ablasi():
    """Pengaruh fitur pencarian kata kunci (keahlian dosen di profil, perluasan sinonim) pada 30 query uji.
    Hasil: eval/hasil_ablasi.csv. Catatan: query uji berupa judul skripsi lengkap, jadi tabel ini terutama
    memeriksa bahwa fitur baru tidak merusak hasil, bukan mengukur pencarian dengan kata kunci pendek."""
    lecturers, pubs, theses = load_data()
    theses = theses.copy()
    theses["thesis_id"] = theses["thesis_id"].astype(str)
    ids = pd.read_csv(OUT / "query_uji_manual.csv", dtype=str)["thesis_id"].tolist()
    test = theses.drop_duplicates("thesis_id")
    test = test[test["thesis_id"].isin(ids)]
    truth = theses[theses["thesis_id"].isin(ids)].groupby("thesis_id")["lecturer_id"].agg(set).to_dict()
    train = theses[~theses["thesis_id"].isin(ids)]
    konfig = [("gabungan", 1, False), ("gabungan", 1, True),
              ("gabungan+keahlian", 1, False), ("gabungan+keahlian", 2, False), ("gabungan+keahlian", 3, False),
              ("gabungan+keahlian", 1, True)]
    rows = []
    for profile, bobot, exp in konfig:
        rec = Recommender(lecturers, pubs, train, profile=profile, bobot_keahlian=bobot)
        for model in ("TF-IDF", "BM25"):
            ranks = []
            for _, r in test.iterrows():
                order = [x["id"] for x in rec.recommend(r["judul"], model=model, k=len(lecturers), expand=exp)]
                pos = [order.index(l) + 1 for l in truth[r["thesis_id"]] if l in order]
                ranks.append(min(pos) if pos else None)
            rows.append({"profil": profile, "bobot_keahlian": bobot if "keahlian" in profile else 0,
                         "perluasan_sinonim": "ya" if exp else "tidak", "model": model, **metrics(ranks)})
    df = pd.DataFrame(rows).round(3)
    df.to_csv(OUT / "hasil_ablasi.csv", index=False)
    print(df.to_string(index=False))
    return df


if __name__ == "__main__":
    import sys
    run_ablasi() if "--ablasi" in sys.argv else run()
