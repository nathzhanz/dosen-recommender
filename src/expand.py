"""Perluasan query dengan sinonim Indonesia-Inggris, supaya pencarian tidak harus sama persis dengan judul.

Cara kerja: setiap kelompok berisi istilah yang setara. Kalau query memuat salah satu istilah,
istilah lain dalam kelompok yang sama ditambahkan ke query. Kamus ini kecil dan ditulis tangan
(bidang informatika/TI), jadi mudah dibaca dan diubah anggota kelompok.
Istilah berawalan "-" hanya memicu perluasan dan tidak ditambahkan ke query (terlalu umum, bisa membuat hasil melenceng).
"""
import re

KELOMPOK = [
    ("sentimen", "sentiment", "-opini", "opinion"),
    ("jaringan komputer", "computer network", "-networking", "-network"),
    ("keamanan jaringan", "network security", "cybersecurity", "keamanan siber", "cyber security"),
    ("keamanan informasi", "information security", "kriptografi", "cryptography", "enkripsi", "encryption"),
    ("kecerdasan buatan", "artificial intelligence", "-artificial"),
    ("-pembelajaran mesin", "machine learning", "deep learning"),
    ("penambangan data", "data mining", "-mining"),
    ("klasifikasi", "classification"),
    ("klaster", "clustering", "pengelompokan", "cluster"),
    ("prediksi", "prediction", "peramalan", "forecasting"),
    ("basis data", "database"),
    ("antarmuka pengguna", "user interface", "ui ux", "ui/ux", "pengalaman pengguna", "user experience",
     "usability", "-kegunaan", "-user centered design"),
    ("sistem pendukung keputusan", "decision support system", "spk", "dss"),
    ("sistem pakar", "expert system"),
    ("pengolahan citra", "image processing", "citra", "visi komputer", "computer vision"),
    ("pengolahan bahasa alami", "natural language processing", "nlp", "-teks", "text mining"),
    ("realitas tertambah", "augmented reality", "realitas virtual", "virtual reality"),
    ("internet of things", "iot", "internet benda", "-sensor"),
    ("e-learning", "pembelajaran daring", "online learning", "pembelajaran elektronik", "e-modul", "emodul"),
    ("media pembelajaran", "learning media", "teknologi pendidikan", "educational technology", "-pendidikan"),
    ("rekayasa perangkat lunak", "software engineering", "pengembangan perangkat lunak", "-software"),
    ("manajemen proyek", "project management"),
    ("tata kelola", "governance", "audit sistem informasi", "information system audit"),
    ("sistem informasi", "information system"),
    ("manajemen pengetahuan", "knowledge management"),
    ("chatbot", "asisten virtual", "retrieval augmented generation", "rag"),
    ("temu kembali informasi", "information retrieval", "-pencarian", "search engine"),
    ("data besar", "big data", "sains data", "data science"),
    ("pemerintahan elektronik", "e-government", "smart government", "it government"),
    ("aplikasi seluler", "mobile application", "android", "aplikasi mobile"),
    ("situs web", "website", "web engineering", "aplikasi web"),
    ("jaringan sensor nirkabel", "wireless sensor network", "nirkabel", "wireless"),
    ("gamifikasi", "gamification", "permainan edukasi", "game edukasi", "-game"),
    ("animasi", "animation", "multimedia"),
]


def _ada(teks: str, istilah: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(istilah) + r"(?![a-z0-9])", teks) is not None


def perluas(query: str) -> tuple[str, list[str]]:
    """Kembalikan (query yang sudah diperluas, daftar istilah yang ditambahkan)."""
    q = " " + re.sub(r"\s+", " ", query.lower()) + " "
    tambahan = []
    for kel in KELOMPOK:
        pemicu = [t.lstrip("-") for t in kel]
        if any(_ada(q, t) for t in pemicu):
            tambahan += [t for t in kel if not t.startswith("-") and not _ada(q, t) and t not in tambahan]
    return (query + " " + " ".join(tambahan)).strip(), tambahan
