"""Pre-processing teks bahasa Indonesia: normalisasi, tokenisasi, stopword, stemming (Sastrawi)."""
import re
from functools import lru_cache

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

_stemmer = StemmerFactory().create_stemmer()

# Stopword Sastrawi + tambahan yang umum pada judul skripsi/publikasi
STOPWORDS = set(StopWordRemoverFactory().get_stop_words()) | {
    "studi", "kasus", "analisis", "penerapan", "implementasi", "rancang", "bangun",
    "pengembangan", "berbasis", "menggunakan", "metode", "sistem", "pada", "untuk",
    "terhadap", "dengan", "of", "the", "and", "in", "for", "using", "based",
}


def normalize(text: str) -> str:
    """Lowercase, hapus URL/angka/tanda baca, rapikan spasi."""
    text = str(text).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return normalize(text).split()


@lru_cache(maxsize=200_000)
def _stem(token: str) -> str:
    return _stemmer.stem(token)


def preprocess(text: str) -> list[str]:
    """Pipeline lengkap -> daftar term (stem)."""
    out = []
    for tok in tokenize(text):
        if tok in STOPWORDS or len(tok) < 3:
            continue
        stem = _stem(tok)
        if stem and stem not in STOPWORDS and len(stem) >= 3:
            out.append(stem)
    return out
