# Menjadikan aplikasi sebuah web (tanpa login untuk pengguna)

Pengguna **tidak perlu login** untuk membuka aplikasi Streamlit yang di-deploy sebagai *public app*.
Hanya orang yang men-deploy (pemilik repo GitHub) yang login satu kali. Hasilnya berupa link
`https://nama-app.streamlit.app` yang bisa dibuka siapa saja dari HP atau laptop.

## Langkah (Streamlit Community Cloud, gratis)

1. **Pastikan repo siap.** Di GitHub, repo harus berisi `app.py`, `requirements.txt`, folder `src/`,
   folder `data/` (3 file CSV), dan folder `.streamlit/`. Repo sebaiknya **public**.
2. Buka <https://share.streamlit.io> lalu klik **Continue with GitHub** dan login dengan akun pemilik repo.
3. Klik **Create app** -> **Deploy a public app from GitHub**.
4. Isi:
   - Repository: `nathzhanz/dosen-recommender`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: pilih nama singkat, misalnya `dosen-pembimbing-unj`
5. Klik **Advanced settings** -> pilih **Python 3.11** (atau 3.12) -> **Save**.
6. Klik **Deploy**. Tunggu 3-5 menit sampai aplikasi muncul.
7. Salin link-nya dan taruh di bagian atas `README.md` (misalnya "Demo: https://...").

## Setelah jadi
- **Tidak perlu login** bagi yang membuka, asalkan app berstatus public
  (menu app -> **Settings** -> **Sharing** -> *This app is public*).
- Aplikasi gratis akan "tidur" bila lama tidak dibuka. Buka sekali sebelum presentasi; kalau muncul tombol
  "Yes, get this app back up!", klik saja.
- Setiap kali kamu mengunggah perubahan ke GitHub, aplikasi diperbarui otomatis.
- Buka pertama kali bisa agak lambat (index dibangun sekali, lalu disimpan di memori).

## Alternatif
- **Hugging Face Spaces** (SDK Streamlit): buat Space baru, unggah isi repo; tidak perlu akun bagi pengunjung.
- Tetap bisa dijalankan lokal: `streamlit run app.py`.

## Yang perlu dicek sebelum dipublikasikan
- Data hanya memuat judul publikasi, judul skripsi tanpa nama mahasiswa, dan data dosen yang memang publik.
- Tidak ada password, token, atau berkas pribadi di repo.
- Cek aturan kampus/dosen pengampu sebelum repo dan aplikasi dibuat public.
