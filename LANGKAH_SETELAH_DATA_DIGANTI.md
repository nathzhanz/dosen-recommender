# Langkah setelah data diganti / diperbarui

Dipakai setiap kali ada data baru (dosen, publikasi, atau skripsi bertambah atau berubah).

1. **Siapkan masukan** di `data_collection/out/`:
   - `theses_raw.csv`: `eprint_id, judul, tahun, prodi, pembimbing` (pembimbing dipisah ` | `, TANPA nama mahasiswa)
   - `sinta_publications.csv`: `nama_dosen, judul, tahun`
   - (opsional) `alias_nama.csv`: `varian,nama_baku` untuk menyatukan ejaan nama yang berbeda
   - (opsional) `lecturers_info.csv`: `nama_dosen,bidang,kuota`
2. **Bangun dataset**: `python data_collection/build_dataset.py --dry-run` lalu baca `out/laporan_data.txt`
   (pembimbing tanpa publikasi, nama tidak cocok). Perbaiki sumbernya, ulangi sampai rapi, lalu jalankan
   tanpa `--dry-run` (menulis `data/lecturers.csv`, `publications.csv`, `theses.csv`).
3. **Periksa**: `python data_collection/check_data.py` harus berakhir "AMAN dipakai".
4. **Uji aplikasi**: `streamlit run app.py` (peringatan kuning "DATA CONTOH" harus hilang), coba 3-5 query.
5. **Evaluasi ulang**: `python -m src.evaluate`. Hasil di `eval/` (hasil_evaluasi.csv, query_uji.csv, query_gagal.json).
6. **Catat untuk laporan**: jumlah dosen/publikasi/skripsi, sumber (link), tanggal pengambilan, filter yang dipakai.
7. **Simpan ke GitHub**: unggah `data/*.csv`, `data_collection/out/*.csv`, dan `eval/*`; beri tahu tim.
8. **Update timeline**: isi kolom Progress % (T02, T04, T05, T06 dst).

Aturan: jangan memasukkan nama mahasiswa/NIM; hanya dosen yang punya publikasi yang dipakai.
Catatan: satu skripsi dengan 2 pembimbing menjadi 2 baris di `theses.csv` (thesis_id sama); evaluasi menganggap
benar bila salah satu pembimbing asli muncul di top-k, dan semua barisnya dikeluarkan dari profil saat diuji.
