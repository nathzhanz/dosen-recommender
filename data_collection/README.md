# Pengumpulan data asli (T02, T04, T05)

Sumber: repository.unj.ac.id (skripsi + pembimbing) dan SINTA (publikasi dosen). Keduanya publik.

Daftar sumber (catat di laporan beserta tanggal pengambilan):
- Skripsi S1 Sistem dan Teknologi Informasi (FT): https://repository.unj.ac.id/view/divisions/S1=5FSistem=5Fdan=5FTI/
  (kode prodi untuk skrip: `S1_Sistem_dan_TI`; ini sudah menjadi **default** `collect_unj.py`)
- SINTA: https://sinta.kemdiktisaintek.go.id/ (profil publik dosen)

## Langkah
1. **Skripsi + pembimbing** (otomatis, jalankan di laptop):
   ```
   python data_collection/collect_unj.py --debug 58128      # uji dulu: harus tampil judul + pembimbing
   python data_collection/collect_unj.py                    # S1 Sistem dan TI (42 skripsi)
   python data_collection/collect_unj.py --divisions S1_Sistem_dan_TI S1_Ilmu_Komputer
   ```
   Ganti `UA` di `collect_unj.py` dengan email kelompok. Hasil: `out/theses_raw.csv` (tanpa nama mahasiswa).
2. **Publikasi dosen** (manual, SINTA): buka profil SINTA tiap nama di `out/theses_raw.csv` (kolom pembimbing),
   salin judul + tahun publikasi ke `out/sinta_publications.csv` (kolom: nama_dosen, judul, tahun).
   Hapus baris CONTOH. Minimal 3 publikasi per dosen.
3. (Opsional) `out/lecturers_info.csv`: `nama_dosen,bidang,kuota` (bidang dari profil SINTA; kuota perkiraan).
4. **Gabungkan**: `python data_collection/build_dataset.py --dry-run` (lihat laporan), lalu tanpa `--dry-run` (menulis ke `data/`).
   Laporan `out/laporan_data.txt` menunjukkan pembimbing yang belum punya publikasi.
5. **Periksa**: `python data_collection/check_data.py` harus berakhir dengan "AMAN dipakai".

Catatan: `build_dataset.py` hanya memakai skripsi yang pembimbingnya punya publikasi, jadi tiap dosen di dataset
pasti punya profil publikasi.
