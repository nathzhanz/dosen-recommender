# Rekomendasi Calon Dosen Pembimbing (Topik 4)

Tugas Project Temu Kembali Informasi, Prodi Sistem dan Teknologi Informasi, UNJ.
Sistem menerima ide judul/topik skripsi lalu merangking dosen yang paling sesuai, lengkap dengan penjelasan (kata kunci dan judul pendukung).

## Komponen
| Komponen | File |
|---|---|
| Pre-processing (normalisasi, tokenisasi, stopword, stemming Sastrawi) | `src/preprocess.py` |
| Inverted index buatan sendiri | `src/index.py` |
| Model ranking: TF-IDF (cosine) dan BM25 | `src/ranking.py` |
| Profil dosen (publikasi + skripsi), ranking, penjelasan, beban bimbingan | `src/recommender.py` |
| Evaluasi hold-out (Success@1, Success@3, MRR) | `src/evaluate.py` |
| Antarmuka web | `app.py` (Streamlit) |

## Cara menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py                  # tanpa data asli otomatis memakai data/sample (sintetis, ada peringatan di layar)
python -m src.evaluate                # hasil di folder eval/
```

## Data
- `data/sample/` = data **sintetis** untuk uji coba (jangan masuk laporan).
- `data/` (lecturers.csv, publications.csv, theses.csv) = **data asli**. Kalau file ini ada, sistem otomatis memakainya.
- Cara membuat data asli (repo UNJ + SINTA): lihat `data_collection/README.md`.
- Periksa sebelum dipakai/dikumpulkan: `python data_collection/check_data.py`.

Format kolom:
- `lecturers.csv`: `id, nama, bidang, kuota`
- `publications.csv`: `lecturer_id, judul, tahun`
- `theses.csv`: `thesis_id, judul, lecturer_id, tahun` (**tanpa nama mahasiswa**)

Patuhi izin dan ketentuan situs sumber; gunakan hanya informasi publik atau data teranonimkan.

## Evaluasi
Judul skripsi lama dijadikan query (30 query, dipilih merata antar dosen). Skripsi uji dikeluarkan dari profil agar tidak bocor. Dibandingkan 2 model x 2 representasi profil. Hasil: `eval/hasil_evaluasi.csv`, query uji: `eval/query_uji.csv`, query gagal: `eval/query_gagal.json`.

## Penggunaan alat AI
Kerangka kode awal dibuat dengan bantuan Claude (Anthropic). Setiap anggota wajib memahami dan mampu menjelaskan seluruh kode. Cantumkan juga di laporan.
