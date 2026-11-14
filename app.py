"""Antarmuka web (Streamlit): masukkan ide judul/topik skripsi -> rekomendasi dosen pembimbing.
Jalankan: streamlit run app.py
"""
import streamlit as st

from src.recommender import Recommender, load_data, using_sample_data

st.set_page_config(page_title="Rekomendasi Dosen Pembimbing", page_icon=None, layout="wide")

CONTOH = {  # label pendek -> query lengkap
    "Sentimen media sosial": "analisis sentimen media sosial menggunakan machine learning",
    "UI/UX aplikasi": "perancangan UI/UX aplikasi pembelajaran dengan metode user centered design",
    "Jaringan mikrotik": "monitoring jaringan komputer berbasis mikrotik",
    "Prediksi penyakit": "prediksi penyakit menggunakan algoritma klasifikasi",
    "E-modul interaktif": "pengembangan e-modul interaktif untuk pembelajaran",
}

st.title("Rekomendasi Calon Dosen Pembimbing")
st.caption("Temu Kembali Informasi - Prodi Sistem dan Teknologi Informasi, UNJ. "
           "Masukkan ide judul skripsi, sistem merangking dosen berdasarkan kemiripan dengan "
           "publikasi dan skripsi yang pernah dibimbing.")
if using_sample_data():
    st.warning("Memakai DATA CONTOH SINTETIS (Dosen A-K). Letakkan data asli di folder data/ "
               "(lecturers.csv, publications.csv, theses.csv) agar sistem memakainya.")


@st.cache_resource
def get_recommender(profile: str):
    lecturers, pubs, theses = load_data()
    return Recommender(lecturers, pubs, theses, profile=profile)


# ---------- Sidebar ----------
with st.sidebar:
    st.header("Pengaturan")
    model = st.radio("Model ranking", ["BM25", "TF-IDF"],
                     help="BM25 dan TF-IDF adalah dua cara memberi skor kecocokan kata. "
                          "Pada evaluasi kami BM25 sedikit lebih baik.")
    profile = st.radio("Representasi profil dosen", ["gabungan", "publikasi"],
                       help="gabungan = judul publikasi + judul skripsi yang dibimbing. "
                            "publikasi = hanya judul publikasi. (Diabaikan pada mode perbandingan.)")
    bandingkan = st.checkbox("Bandingkan profil berdampingan",
                             help="Tampilkan dua daftar sekaligus: profil publikasi dan profil gabungan.")
    k = st.slider("Jumlah dosen ditampilkan", 1, 10, 3)
    load_w = st.slider("Pertimbangan beban bimbingan", 0.0, 1.0, 0.0, 0.05,
                       help="0 = abaikan beban. Makin besar, dosen yang kuotanya hampir atau sudah penuh "
                            "makin turun peringkatnya.")
    st.divider()
    st.caption("Kuota bimbingan (20 per dosen) adalah asumsi, bukan data resmi.")

# ---------- Input ----------
if "query" not in st.session_state:
    st.session_state["query"] = ""
if "dicari" not in st.session_state:
    st.session_state["dicari"] = False

st.write("**Contoh ide judul** (klik untuk mencoba):")
cols = st.columns(len(CONTOH))
for c, (label, contoh) in zip(cols, CONTOH.items()):
    if c.button(label, use_container_width=True, key="contoh_" + label, help=contoh):
        st.session_state["query"] = contoh
        st.session_state["dicari"] = True

with st.form("form_cari", border=False):
    st.text_area("Ide judul atau topik skripsi", key="query", height=90,
                 placeholder="contoh: klasifikasi citra penyakit daun menggunakan CNN")
    kirim = st.form_submit_button("Cari dosen", type="primary")
if kirim:
    st.session_state["dicari"] = True


# ---------- Tampilan hasil ----------
def tampilkan(rec, results, query):
    """Daftar dosen: skor, beban bimbingan, kata kunci, dan judul pendukung."""
    if not results:
        st.warning("Tidak ada dosen yang cocok. Coba kata kunci lain atau lebih spesifik.")
        return
    top = results[0]["skor"] or 1.0
    for i, r in enumerate(results, 1):
        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 2, 2])
            c1.subheader(f"{i}. {r['nama']}")
            c1.caption(f"Bidang: {r['bidang']}")
            c2.metric("Skor", f"{r['skor']:.3f}")
            c2.progress(min(r["skor"] / top, 1.0), text=f"{r['skor'] / top:.0%} dari skor tertinggi")
            terpakai, kuota = (int(x) for x in r["beban"].split("/"))
            c3.metric("Beban bimbingan", r["beban"],
                      delta="melebihi kuota" if terpakai > kuota else None, delta_color="inverse")
            ex = rec.explain(query, r["id"])
            kata = ", ".join(f"`{t}`" for t in ex["kata_kunci"]) or "-"
            st.markdown("**Kata kunci yang cocok** (bentuk dasar): " + kata)
            if ex["judul_pendukung"]:
                with st.expander(f"Judul pendukung ({len(ex['judul_pendukung'])})"):
                    for it in ex["judul_pendukung"]:
                        st.write(f"- ({it['sumber']}) {it['judul']}")


query = st.session_state["query"].strip()
if st.session_state["dicari"] and not query:
    st.info("Tulis ide judul atau pilih salah satu contoh di atas.")
elif st.session_state["dicari"] and query:
    st.divider()
    if bandingkan:
        st.info(f"Mode perbandingan: query yang sama dihitung dari dua representasi profil (model: {model}).")
        kiri, kanan = st.columns(2)
        for kolom, nama_profil in ((kiri, "publikasi"), (kanan, "gabungan")):
            with kolom:
                st.header("Profil publikasi saja" if nama_profil == "publikasi" else "Profil gabungan")
                rec = get_recommender(nama_profil)
                tampilkan(rec, rec.recommend(query, model=model, k=k, load_weight=load_w), query)
    else:
        st.subheader(f"Hasil: model {model}, profil {profile}")
        rec = get_recommender(profile)
        tampilkan(rec, rec.recommend(query, model=model, k=k, load_weight=load_w), query)
    with st.expander("Cara membaca hasil"):
        st.markdown(
            "- **Skor**: makin tinggi makin cocok. Skor hanya bisa dibandingkan dalam satu pencarian.\n"
            "- **Beban bimbingan**: jumlah skripsi yang pernah dibimbing dibanding kuota (asumsi).\n"
            "- **Kata kunci**: kata dari query yang paling berkontribusi pada skor dosen tersebut "
            "(selalu dihitung dari kontribusi BM25, juga saat model TF-IDF dipilih).\n"
            "- **Judul pendukung**: judul publikasi atau skripsi dosen yang memuat kata dari query.")
