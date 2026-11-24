"""Gabungkan skripsi (UNJ) + publikasi (SINTA) menjadi tiga CSV untuk sistem rekomendasi.

Masukan (taruh di data_collection/out/):
  theses_raw.csv            -> hasil collect_unj.py (eprint_id, judul, tahun, prodi, pembimbing 'A | B')
  sinta_publications.csv    -> disalin manual dari profil SINTA: nama_dosen, judul, tahun
  (opsional) lecturers_info.csv -> nama_dosen, bidang, kuota, pakar, rumpun_kbi   (dibuat dari dosen.csv; kalau tidak ada: bidang dari prodi skripsi, kuota=20)

Aturan: hanya dosen yang PUNYA publikasi (>= --min-pub) yang dipakai. Skripsi yang pembimbingnya tidak
punya publikasi dibuang dan dilaporkan di out/laporan_data.txt.
Hasil: data/lecturers.csv, data/publications.csv, data/theses.csv (tanpa nama mahasiswa).
"""
import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).parent / "out"


def norm(name: str) -> str:
    """Kunci pencocokan nama: buang gelar, tanda baca, huruf kecil."""
    name = str(name).split(",")[0]
    name = re.sub(r"\b(dr|prof|ir|drs|dra|h|hj)\b\.?", " ", name, flags=re.I)
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


def load_alias():
    """out/alias_nama.csv (varian,nama_baku): menyatukan ejaan/variasi nama yang sama."""
    f = OUT / "alias_nama.csv"
    if not f.exists():
        return {}
    a = pd.read_csv(f, dtype=str).fillna("")
    return {norm(v): norm(b) for v, b in zip(a["varian"], a["nama_baku"]) if v and b}


ALIAS = {}


def nk(name: str) -> str:
    k = norm(name)
    return ALIAS.get(k, k)


def main():
    global ALIAS
    ALIAS = load_alias()
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-pub", type=int, default=1, help="minimal publikasi per dosen (default 1)")
    ap.add_argument("--kuota", type=int, default=20, help="kuota bimbingan default (ASUMSI, ganti bila ada data)")
    ap.add_argument("--hanya-pembimbing", action="store_true",
                    help="hanya dosen yang pernah membimbing skripsi (default: dosen berpublikasi tanpa skripsi ikut, beban 0)")
    ap.add_argument("--dry-run", action="store_true", help="hanya laporan, jangan menimpa data/*.csv")
    args = ap.parse_args()

    th = pd.read_csv(OUT / "theses_raw.csv", dtype=str).fillna("")
    pub = pd.read_csv(OUT / "sinta_publications.csv", dtype=str).fillna("")
    info_f = OUT / "lecturers_info.csv"
    info = pd.read_csv(info_f, dtype=str).fillna("") if info_f.exists() else pd.DataFrame(columns=["nama_dosen", "bidang", "kuota", "pakar", "rumpun_kbi"])

    pub["key"] = pub["nama_dosen"].map(nk)
    pub = pub[pub["judul"].str.strip() != ""].drop_duplicates(["key", "judul"])
    if "prodi" not in th.columns:
        th["prodi"] = ""
    pub_count = pub.groupby("key").size()
    eligible = set(pub_count[pub_count >= args.min_pub].index)

    # satu baris skripsi per (skripsi, pembimbing); pembimbing pertama = pembimbing utama
    rows = []
    for _, r in th.iterrows():
        advs = [a.strip() for a in r["pembimbing"].split("|") if a.strip()]
        for i, a in enumerate(advs):
            rows.append({"eprint_id": r["eprint_id"], "judul": r["judul"], "tahun": r["tahun"],
                         "pembimbing": a, "key": nk(a), "urutan": i + 1})
    tr = pd.DataFrame(rows)
    laporan = []
    if tr.empty:
        raise SystemExit("theses_raw.csv tidak punya pembimbing terbaca. Jalankan collect_unj.py --debug dulu.")
    tr["ada_publikasi"] = tr["key"].isin(eligible)

    adv_all = tr.groupby(["key"]).agg(nama=("pembimbing", "first"), skripsi=("eprint_id", "nunique")).reset_index()
    adv_all["publikasi"] = adv_all["key"].map(pub_count).fillna(0).astype(int)
    adv_all["dipakai"] = adv_all["key"].isin(eligible)
    laporan.append("PEMBIMBING DAN JUMLAH PUBLIKASI (SINTA)\n" + adv_all.sort_values("skripsi", ascending=False)
                   .to_string(index=False))
    missing = adv_all[~adv_all["dipakai"]]
    laporan.append(f"\nPembimbing TANPA/KURANG publikasi (< {args.min_pub}) -> perlu dilengkapi dari SINTA atau dibuang:\n" +
                   (missing[["nama", "skripsi", "publikasi"]].to_string(index=False) if len(missing) else "(tidak ada)"))
    unmatched = sorted(set(pub["key"]) - set(adv_all["key"]))
    laporan.append("\nNama di sinta_publications.csv yang bukan pembimbing skripsi mana pun (ikut sebagai dosen tanpa riwayat bimbingan, "
                   "beban 0; periksa ejaan bila tidak diharapkan): " + (", ".join(unmatched) if unmatched else "(tidak ada)"))

    # pakai pembimbing utama (urutan 1) kalau layak; kalau tidak, pembimbing layak lainnya
    keep = tr[tr["ada_publikasi"]].sort_values(["eprint_id", "urutan"]).drop_duplicates(["eprint_id", "key"])
    dropped = th[~th["eprint_id"].isin(keep["eprint_id"])]
    laporan.append(f"\nSkripsi dipakai: {keep['eprint_id'].nunique()} dari {len(th)} (baris skripsi-pembimbing: {len(keep)}); "
                   f"dibuang karena SEMUA pembimbingnya tanpa publikasi/tidak terbaca: {len(dropped)}")

    lec_keys = sorted(set(keep["key"]) if args.hanya_pembimbing else set(keep["key"]) | eligible)
    key_to_id = {k: f"D{i+1:02d}" for i, k in enumerate(lec_keys)}
    name_of = dict(zip(adv_all["key"], adv_all["nama"]))
    name_of.update(dict(zip(pub["key"], pub["nama_dosen"])))  # nama dari SINTA (lengkap dengan gelar) diutamakan
    info["key"] = info["nama_dosen"].map(nk) if len(info) else []
    info_map = info.set_index("key").to_dict("index") if len(info) else {}
    prodi_by_key = {}
    if "prodi" in th.columns:
        tp = tr.merge(th[["eprint_id", "prodi"]], on="eprint_id")
        prodi_by_key = tp.groupby("key")["prodi"].agg(lambda x: ", ".join(sorted(set(x)))).to_dict()
    lecturers = pd.DataFrame([{"id": key_to_id[k], "nama": name_of[k],
                               "bidang": info_map.get(k, {}).get("bidang", "") or ("Prodi " + prodi_by_key[k] if k in prodi_by_key else "-"),
                               "kuota": info_map.get(k, {}).get("kuota", "") or str(args.kuota),
                               "pakar": info_map.get(k, {}).get("pakar", ""),
                               "rumpun_kbi": info_map.get(k, {}).get("rumpun_kbi", "")} for k in lec_keys])
    publications = pd.DataFrame({"lecturer_id": pub["key"].map(key_to_id), "judul": pub["judul"], "tahun": pub["tahun"]}).dropna(subset=["lecturer_id"])
    theses = pd.DataFrame({"thesis_id": "S" + keep["eprint_id"].astype(str).values, "judul": keep["judul"].values,
                           "lecturer_id": keep["key"].map(key_to_id).values, "tahun": keep["tahun"].values})

    laporan.append(f"\nHASIL: {len(lecturers)} dosen, {len(publications)} publikasi, {len(theses)} skripsi")
    per = theses.groupby("lecturer_id").size()
    laporan.append("Skripsi per dosen: " + ", ".join(f"{k}={v}" for k, v in per.items()))
    text = "\n".join(laporan)
    OUT.mkdir(exist_ok=True)
    (OUT / "laporan_data.txt").write_text(text, encoding="utf-8")
    print(text)
    if not args.dry_run:
        d = ROOT / "data"
        lecturers.to_csv(d / "lecturers.csv", index=False)
        publications.to_csv(d / "publications.csv", index=False)
        theses.to_csv(d / "theses.csv", index=False)
        print("\nCSV ditulis ke", d)


if __name__ == "__main__":
    main()
