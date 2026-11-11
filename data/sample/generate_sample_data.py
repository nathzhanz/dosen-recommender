"""Membuat DATA CONTOH SINTETIS (placeholder) agar pipeline bisa dijalankan dan diuji.

PENTING: data ini BUKAN data nyata. Dosen bernama 'Dosen A..J', judul dibangkitkan dari
template. Untuk tugas sebenarnya, ganti data/publications.csv dan data/theses.csv dengan
data publik asli (SINTA/Google Scholar + daftar skripsi), dengan format kolom yang sama.
Jalankan: python data/sample/generate_sample_data.py
"""
import csv
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent  # menulis ke data/sample/ (bukan data/ asli)

# bidang -> (daftar tugas/objek, daftar teknik, daftar domain penerapan)
AREAS = {
    "Data Mining": (
        ["klasifikasi", "klasterisasi", "prediksi", "deteksi anomali", "analisis sentimen"],
        ["random forest", "k-means", "naive bayes", "support vector machine", "xgboost"],
        ["churn pelanggan", "ulasan aplikasi", "data penjualan", "nilai akademik mahasiswa", "transaksi keuangan"]),
    "Rekayasa Perangkat Lunak": (
        ["pengujian perangkat lunak", "manajemen kebutuhan", "arsitektur microservice", "kualitas kode", "otomasi deployment"],
        ["agile scrum", "test driven development", "continuous integration", "unified modeling language", "clean architecture"],
        ["aplikasi akademik", "sistem informasi perpustakaan", "aplikasi e-commerce", "layanan mobile", "aplikasi pemerintahan"]),
    "Internet of Things": (
        ["pemantauan lingkungan", "otomasi rumah", "irigasi cerdas", "pelacakan aset", "kontrol perangkat jarak jauh"],
        ["esp32", "mqtt", "sensor suhu", "lora", "arduino"],
        ["pertanian hidroponik", "gedung kampus", "kandang ternak", "kualitas udara", "parkir cerdas"]),
    "Interaksi Manusia dan Komputer": (
        ["evaluasi usability", "desain antarmuka pengguna", "pengalaman pengguna", "aksesibilitas", "prototipe interaktif"],
        ["system usability scale", "user centered design", "design thinking", "heuristic evaluation", "eye tracking"],
        ["aplikasi pembelajaran", "layanan kesehatan digital", "portal kampus", "aplikasi lansia", "game edukasi"]),
    "Keamanan Informasi": (
        ["deteksi intrusi", "audit keamanan", "enkripsi data", "analisis kerentanan", "manajemen risiko"],
        ["iso 27001", "penetration testing", "advanced encryption standard", "firewall", "blockchain"],
        ["jaringan kampus", "aplikasi web", "data pribadi", "transaksi digital", "server universitas"]),
    "Pemrosesan Bahasa Alami": (
        ["klasifikasi teks", "ringkasan otomatis", "pencarian dokumen", "tanya jawab", "ekstraksi entitas"],
        ["tf idf", "word2vec", "indobert", "long short term memory", "bm25"],
        ["berita daring", "dokumen hukum", "media sosial", "karya ilmiah", "layanan pelanggan"]),
    "Visi Komputer": (
        ["deteksi objek", "klasifikasi citra", "pengenalan wajah", "segmentasi citra", "pengenalan tulisan tangan"],
        ["convolutional neural network", "yolo", "transfer learning", "augmentasi data", "mobilenet"],
        ["citra medis", "penyakit daun", "presensi mahasiswa", "kendaraan", "kemasan produk"]),
    "Basis Data dan Data Engineering": (
        ["perancangan data warehouse", "optimasi query", "integrasi data", "pipeline etl", "tata kelola data"],
        ["apache spark", "postgresql", "mongodb", "dimensional modeling", "apache airflow"],
        ["data akademik", "data kesehatan", "data logistik", "data keuangan daerah", "data sensus"]),
    "Sistem Informasi dan Tata Kelola TI": (
        ["evaluasi tingkat kematangan", "perencanaan strategis", "audit teknologi informasi", "adopsi teknologi", "transformasi digital"],
        ["cobit", "itil", "technology acceptance model", "enterprise architecture", "balanced scorecard"],
        ["perguruan tinggi", "usaha kecil menengah", "instansi pemerintah", "rumah sakit", "perbankan"]),
    "Sistem Rekomendasi": (
        ["rekomendasi produk", "rekomendasi materi belajar", "rekomendasi wisata", "rekomendasi film", "personalisasi konten"],
        ["collaborative filtering", "content based filtering", "matrix factorization", "cosine similarity", "association rule"],
        ["toko daring", "platform e-learning", "destinasi wisata", "aplikasi musik", "lowongan kerja"]),
    "Komputasi Awan dan Jaringan": (
        ["optimasi kinerja jaringan", "virtualisasi server", "load balancing", "manajemen bandwidth", "migrasi layanan"],
        ["docker", "kubernetes", "software defined network", "quality of service", "openstack"],
        ["layanan kampus", "pusat data", "jaringan nirkabel", "aplikasi streaming", "layanan pemerintah"]),
}

# bidang sekunder (irisan minat) agar data tidak terlalu mudah dipisahkan
SECONDARY = {
    "Data Mining": "Sistem Rekomendasi", "Rekayasa Perangkat Lunak": "Interaksi Manusia dan Komputer",
    "Internet of Things": "Komputasi Awan dan Jaringan", "Interaksi Manusia dan Komputer": "Rekayasa Perangkat Lunak",
    "Keamanan Informasi": "Komputasi Awan dan Jaringan", "Pemrosesan Bahasa Alami": "Data Mining",
    "Visi Komputer": "Data Mining", "Basis Data dan Data Engineering": "Data Mining",
    "Sistem Informasi dan Tata Kelola TI": "Basis Data dan Data Engineering",
    "Sistem Rekomendasi": "Pemrosesan Bahasa Alami", "Komputasi Awan dan Jaringan": "Keamanan Informasi",
}

TEMPLATES = [
    "{task} {domain} menggunakan {tech}",
    "Penerapan {tech} untuk {task} pada {domain}",
    "Analisis {task} {domain} berbasis {tech}",
    "Rancang bangun sistem {task} pada {domain} dengan {tech}",
    "Perbandingan {tech} dalam {task} {domain}",
]


def make_title(area: str) -> str:
    tasks, techs, domains = AREAS[area]
    return random.choice(TEMPLATES).format(
        task=random.choice(tasks), tech=random.choice(techs), domain=random.choice(domains)
    ).capitalize()


def main():
    areas = list(AREAS)
    lecturers = []
    for i, area in enumerate(areas):
        lecturers.append({"id": f"D{i+1:02d}", "nama": f"Dosen {chr(65+i)}", "bidang": area,
                          "kuota": random.choice([12, 14, 16, 18])})
    with open(OUT / "lecturers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "nama", "bidang", "kuota"])
        w.writeheader(); w.writerows(lecturers)

    pubs, theses, used = [], [], set()
    for lec in lecturers:
        for _ in range(8):  # publikasi
            for _ in range(20):
                area = lec["bidang"] if random.random() < 0.85 else SECONDARY[lec["bidang"]]
                t = make_title(area)
                if t not in used:
                    used.add(t); break
            pubs.append({"lecturer_id": lec["id"], "judul": t, "tahun": random.randint(2015, 2025)})
        n_thesis = random.randint(10, 16)
        for j in range(n_thesis):  # skripsi bimbingan (nama mahasiswa TIDAK disimpan)
            for _ in range(20):
                area = lec["bidang"] if random.random() < 0.8 else SECONDARY[lec["bidang"]]
                t = make_title(area)
                if t not in used:
                    used.add(t); break
            theses.append({"thesis_id": f"S{len(theses)+1:03d}", "judul": t,
                           "lecturer_id": lec["id"], "tahun": random.randint(2018, 2025)})
    for name, rows in (("publications", pubs), ("theses", theses)):
        with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"{len(lecturers)} dosen, {len(pubs)} publikasi, {len(theses)} skripsi")


if __name__ == "__main__":
    main()
