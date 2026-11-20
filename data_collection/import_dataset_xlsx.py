"""Ubah Dataset_Publikasi_Dosen.xlsx (satu sheet per dosen) menjadi sinta_publications.csv.

Jalankan:  python data_collection/import_dataset_xlsx.py
Lalu:      python data_collection/build_dataset.py  &&  python -m src.evaluate
Kolom xlsx: No, Nama, Sumber, Judul, Tahun. Judul ganda dalam satu dosen dihapus,
teks yang rusak karena pengkodean (mis. 'NAÃ\x8fVE') diperbaiki, tahun di luar 1990-2026 dilaporkan.
"""
import re
from pathlib import Path

import openpyxl
import pandas as pd

OUT = Path(__file__).resolve().parent / "out"
SRC = OUT / "Dataset_Publikasi_Dosen.xlsx"
TAHUN_KOREKSI = {2925: 2025}  # salah ketik yang sudah dikonfirmasi (Vannisa Irma Dewi)


def perbaiki(teks: str) -> str:
    teks = str(teks).strip()
    if re.search("Ã|â€|Â", teks):
        for enc in ("latin1", "cp1252"):
            try:
                return teks.encode(enc).decode("utf8")
            except Exception:
                pass
        teks = re.sub(r"NA.{1,6}VE", "NAIVE", teks)
    return teks


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    baris = []
    for ws in wb:
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i == 0 or r is None or len(r) < 4 or not r[3] or not str(r[3]).strip():
                continue
            baris.append({"nama_dosen": str(r[1]).strip(), "judul": perbaiki(r[3]),
                          "tahun": r[4] if len(r) > 4 else None, "sumber": str(r[2] or "").strip().lower()})
    df = pd.DataFrame(baris)
    df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce").replace(TAHUN_KOREKSI)
    aneh = df[(df.tahun < 1990) | (df.tahun > 2026)]
    if len(aneh):
        print("PERIKSA tahun aneh:\n", aneh[["nama_dosen", "tahun", "judul"]].to_string())
    df["_k"] = df["judul"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
    n0 = len(df)
    df = df.drop_duplicates(["nama_dosen", "_k"]).drop(columns="_k")
    df["tahun"] = df["tahun"].astype("Int64")
    df.to_csv(OUT / "sinta_publications.csv", index=False)
    print(f"{n0} baris dibaca, {n0 - len(df)} judul ganda dihapus, {len(df)} publikasi, {df.nama_dosen.nunique()} dosen")


if __name__ == "__main__":
    main()
