"""Antarmuka web (Streamlit): masukkan ide judul/topik skripsi -> rekomendasi dosen pembimbing.
Jalankan: streamlit run app.py
"""
import streamlit as st

from src.recommender import Recommender, load_data, using_sample_data

st.set_page_config(page_title="Rekomendasi Dosen Pembimbing", layout="wide")
st.title("Rekomendasi Calon Dosen Pembimbing")
st.caption("Temu Kembali Informasi - Prodi Sistem dan Teknologi Informasi, UNJ.")
if using_sample_data():
    st.warning("Memakai DATA CONTOH SINTETIS (Dosen A-K). Letakkan data asli di folder data/ "
               "(lecturers.csv, publications.csv, theses.csv) agar sistem memakainya.")


@st.cache_resource
def get_recommender(profile: str):
    lecturers, pubs, theses = load_data()
    return Recommender(lecturers, pubs, theses, profile=profile)


with st.sidebar:
    st.header("Pengaturan")
    model = st.radio("Model ranking", ["BM25", "TF-IDF"])
    profile = st.radio("Representasi profil dosen", ["gabungan", "publikasi"],
                       help="gabungan = judul publikasi + skripsi bimbingan")
    k = st.slider("Jumlah dosen ditampilkan", 1, 10, 3)
    load_w = st.slider("Pertimbangan beban bimbingan", 0.0, 1.0, 0.0, 0.05,
                       help="0 = abaikan beban; makin besar, dosen dengan kuota penuh makin turun")

query = st.text_area("Ide judul atau topik skripsi", height=90,
                     placeholder="contoh: klasifikasi citra penyakit daun menggunakan CNN")

if st.button("Cari dosen", type="primary") and query.strip():
    rec = get_recommender(profile)
    results = rec.recommend(query, model=model, k=k, load_weight=load_w)
    if not results:
        st.warning("Tidak ada dosen yang cocok. Coba kata kunci lain.")
    for i, r in enumerate(results, 1):
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.subheader(f"{i}. {r['nama']}")
            c1.write(f"Bidang: {r['bidang']}")
            c2.metric("Skor", f"{r['skor']:.3f}")
            c3.metric("Beban", r["beban"])
            ex = rec.explain(query, r["id"])
            st.write("**Kata kunci yang cocok:** " + (", ".join(ex["kata_kunci"]) or "-"))
            for it in ex["judul_pendukung"]:
                st.write(f"- ({it['sumber']}) {it['judul']}")
