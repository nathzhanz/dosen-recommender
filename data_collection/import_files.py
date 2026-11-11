"""Ubah file hasil kumpulan tim menjadi masukan build_dataset.py.

  python data_collection/import_files.py --theses skripsi_gabungan.xlsx --pubs Publikasi_Dosen.csv

--theses : Excel dengan sheet skripsi_ptik, skripsi_sti (kolom: id, judul, tahun, pembimbing_1, pembimbing_2, ...)
--pubs   : CSV publikasi (kolom: Nama, SINTA ID, Sumber, Judul, Tahun)
Menulis out/theses_raw.csv dan out/sinta_publications.csv. Kolom abstrak/url TIDAK dibawa (tidak diperlukan).
"""
import argparse
import re
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "out"
SHEETS = {"skripsi_ptik": "PTIK", "skripsi_sti": "STI"}


def fix_text(s: str) -> str:
    s = str(s).strip()
    if re.search(r"[ÃÂâ][\x80-\xbf€-Ÿ]?", s):
        try:
            s = s.encode("cp1252").decode("utf-8")
        except Exception:
            s = re.sub(r"[ÃÂâ][^\sA-Za-z]{0,2}", "", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theses", required=True)
    ap.add_argument("--pubs", required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for sheet, prodi in SHEETS.items():
        d = pd.read_excel(a.theses, sheet_name=sheet, dtype=str).fillna("")
        for _, r in d.iterrows():
            advs = [x.strip() for x in (r["pembimbing_1"], r["pembimbing_2"]) if x.strip()]
            rows.append({"eprint_id": r["id"], "judul": fix_text(r["judul"]), "tahun": r["tahun"],
                         "prodi": prodi, "pembimbing": " | ".join(advs)})
    th = pd.DataFrame(rows).drop_duplicates("eprint_id")
    th.to_csv(OUT / "theses_raw.csv", index=False)

    p = pd.read_csv(a.pubs, dtype=str).fillna("")
    pub = pd.DataFrame({"nama_dosen": p["Nama"].str.strip(), "judul": p["Judul"].map(fix_text),
                        "tahun": p["Tahun"], "sinta_id": p.get("SINTA ID", ""), "sumber": p.get("Sumber", "")})
    pub.to_csv(OUT / "sinta_publications.csv", index=False)
    print(f"skripsi: {len(th)} ({th['prodi'].value_counts().to_dict()}), publikasi: {len(pub)} dari {pub['nama_dosen'].nunique()} dosen")


if __name__ == "__main__":
    main()
