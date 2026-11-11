"""Periksa tiga CSV di data/ sebelum dipakai/dikumpulkan.  Jalankan: python data_collection/check_data.py"""
import sys
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent.parent / "data"
ok = True


def fail(msg):
    global ok
    ok = False
    print("GAGAL :", msg)


def good(msg):
    print("ok    :", msg)


try:
    L = pd.read_csv(D / "lecturers.csv", dtype=str).fillna("")
    P = pd.read_csv(D / "publications.csv", dtype=str).fillna("")
    T = pd.read_csv(D / "theses.csv", dtype=str).fillna("")
except FileNotFoundError as e:
    sys.exit(f"GAGAL : {e.filename} tidak ada. Data asli belum dibuat (lihat data_collection/README.md).")

for name, df, cols in (("lecturers", L, ["id", "nama", "bidang", "kuota"]),
                       ("publications", P, ["lecturer_id", "judul", "tahun"]),
                       ("theses", T, ["thesis_id", "judul", "lecturer_id", "tahun"])):
    if list(df.columns) != cols:
        fail(f"{name}.csv kolom harus persis {cols}, sekarang {list(df.columns)}")
    else:
        good(f"{name}.csv kolom benar ({len(df)} baris)")

bad_cols = [c for df in (L, P, T) for c in df.columns if any(k in c.lower() for k in ("mahasiswa", "penulis", "creator", "nim"))]
if bad_cols:
    fail(f"ada kolom yang mungkin berisi data mahasiswa: {bad_cols} (hapus!)")
else:
    good("tidak ada kolom nama mahasiswa/NIM")

if L["nama"].str.contains(r"^Dosen [A-Z]$", regex=True).any():
    fail("masih ada 'Dosen A-K' (data sintetis)")
if not set(P["lecturer_id"]) <= set(L["id"]) or not set(T["lecturer_id"]) <= set(L["id"]):
    fail("ada lecturer_id di publications/theses yang tidak ada di lecturers.csv")
else:
    good("semua lecturer_id valid")
no_pub = sorted(set(L["id"]) - set(P["lecturer_id"]))
if no_pub:
    fail(f"dosen tanpa publikasi: {no_pub}")
else:
    good("setiap dosen punya publikasi")
few = P.groupby("lecturer_id").size()
if (few < 3).any():
    print("catatan: dosen dengan < 3 publikasi:", list(few[few < 3].index))
for name, df, col in (("publications", P, "judul"), ("theses", T, "judul")):
    if (df[col].str.strip() == "").any():
        fail(f"{name}.csv ada judul kosong")
    if df[col].duplicated().any():
        print(f"catatan: {name}.csv ada judul ganda ({int(df[col].duplicated().sum())})")
n_t = len(T)
print(f"\nRingkasan: {len(L)} dosen, {len(P)} publikasi, {n_t} skripsi")
if n_t < 30:
    print("catatan: skripsi < 30, query uji otomatis akan lebih sedikit; tambah prodi (Ilmu Komputer / PTIK).")
print("\nHASIL:", "AMAN dipakai" if ok else "ADA MASALAH, perbaiki dulu")
sys.exit(0 if ok else 1)
