"""Antarmuka web (Streamlit): ide judul atau kata kunci topik -> rekomendasi dosen pembimbing.
Jalankan lokal: streamlit run app.py   |   Untuk web publik: lihat DEPLOY.md
"""
import html
import re

import streamlit as st

from src.expand import perluas
from src.preprocess import preprocess
from src.recommender import Recommender, load_data, using_sample_data

st.set_page_config(page_title="Rekomendasi Dosen Pembimbing", page_icon="🎓", layout="centered")

SATUDATA = "https://satudata.unj.ac.id/kepegawaian-dan-umum/temukan-pegawai"
PROFIL = {"Publikasi saja": "publikasi",
          "Publikasi + skripsi": "gabungan",
          "Publikasi + skripsi + keahlian": "gabungan+keahlian"}
CONTOH = {
    "Sentimen media sosial": "analisis sentimen media sosial menggunakan machine learning",
    "UI/UX aplikasi": "perancangan UI/UX aplikasi pembelajaran dengan metode user centered design",
    "Jaringan & keamanan": "keamanan jaringan komputer pada infrastruktur kampus",
    "Prediksi penyakit": "prediksi penyakit menggunakan algoritma klasifikasi",
    "E-modul interaktif": "pengembangan e-modul interaktif untuk pembelajaran",
}

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 860px;}
.hero h1 {font-size: 2rem; margin-bottom: .1rem;}
.hero p {opacity: .75; margin-top: 0;}
.chip {display:inline-block; padding: 2px 10px; margin: 2px 4px 2px 0; border-radius: 999px;
       font-size: .8rem; border: 1px solid rgba(128,128,128,.35); background: rgba(128,128,128,.10);}
.chip.cocok {background: rgba(46,160,67,.18); border-color: rgba(46,160,67,.6); font-weight: 600;}
.chip.rumpun {background: rgba(56,120,255,.14); border-color: rgba(56,120,255,.5);}
.rank {display:inline-block; width: 2rem; height: 2rem; line-height: 2rem; text-align:center;
       border-radius: 50%; background: #2b5fd9; color: #fff; font-weight: 700; margin-right: .6rem;}
.nama {font-size: 1.15rem; font-weight: 700;}
.sub {opacity: .7; font-size: .85rem; margin: .1rem 0 .5rem 2.6rem;}
.bar {height: 8px; border-radius: 6px; background: rgba(128,128,128,.22); overflow: hidden; margin: 2px 0 6px 0;}
.bar > div {height: 100%; border-radius: 6px;}
.lbl {font-size: .78rem; opacity: .7; margin-top: .4rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🎓 Rekomendasi Calon Dosen Pembimbing</h1>'
            '<p>Tulis ide judul atau pilih topik, sistem merangking dosen yang paling dekat dengan topikmu '
            'berdasarkan publikasi, skripsi yang pernah dibimbing, dan bidang keahliannya.</p></div>',
            unsafe_allow_html=True)
if using_sample_data():
    st.warning("Memakai DATA CONTOH SINTETIS. Letakkan data asli di folder data/ agar sistem memakainya.")


@st.cache_resource
def get_recommender(profile: str):
    lecturers, pubs, theses = load_data()
    return Recommender(lecturers, pubs, theses, profile=profile)


@st.cache_data
def daftar_topik():
    """Topik dari kolom 'pakar' (bidang keahlian) semua dosen, diurutkan dari yang paling umum."""
    lecturers, _, _ = load_data()
    hitung = {}
    if "pakar" in lecturers.columns:
        for teks in lecturers["pakar"].dropna():
            for t in str(teks).split(","):
                t = t.strip()
                if len(t) > 2:
                    hitung[t] = hitung.get(t, 0) + 1
    return [t for t, _ in sorted(hitung.items(), key=lambda x: (-x[1], x[0].lower()))]


@st.cache_data
def daftar_filter():
    lecturers, _, _ = load_data()
    prodi = sorted({p.strip() for b in lecturers["bidang"].dropna() for p in str(b).replace("Prodi", "").split(",") if p.strip()})
    rumpun = sorted({str(r) for r in lecturers.get("rumpun_kbi", []) if str(r) not in ("", "nan")})
    return prodi, rumpun


# ---------- Pengaturan ----------
with st.expander("⚙️ Pengaturan pencarian"):
    c1, c2 = st.columns(2)
    model = c1.radio("Model ranking", ["BM25", "TF-IDF"], horizontal=True,
                     help="Dua cara memberi skor kecocokan kata. Pada evaluasi kami BM25 sedikit lebih baik.")
    profil_label = c2.selectbox("Profil dosen", list(PROFIL), index=2,
                                help="Teks yang dipakai untuk mewakili tiap dosen. 'keahlian' = bidang keahlian dan rumpun "
                                     "dari data dosen, membantu pencarian dengan kata kunci pendek.")
    sinonim = st.toggle("Perluas dengan sinonim Indonesia-Inggris", value=True,
                        help="Contoh: 'sentimen' juga mencari 'sentiment'. Membantu bila kata di query berbeda dari judul.")
    c3, c4 = st.columns(2)
    k = c3.slider("Jumlah dosen", 1, 10, 3)
    load_w = c4.slider("Pertimbangan beban bimbingan", 0.0, 1.0, 0.0, 0.05,
                       help="0 = abaikan beban. Makin besar, dosen yang kuotanya hampir penuh makin turun peringkatnya.")
    prodi_opsi, rumpun_opsi = daftar_filter()
    f1, f2 = st.columns(2)
    f_prodi = f1.multiselect("Filter prodi", prodi_opsi, placeholder="Semua prodi")
    f_rumpun = f2.multiselect("Filter rumpun KBI", rumpun_opsi, placeholder="Semua rumpun")
    bandingkan = st.checkbox("Bandingkan dua profil berdampingan")
    if bandingkan:
        b1, b2 = st.columns(2)
        kiri_label = b1.selectbox("Kolom kiri", list(PROFIL), index=0)
        kanan_label = b2.selectbox("Kolom kanan", list(PROFIL), index=2)
    st.caption("Kuota bimbingan diambil dari data dosen (dosen.csv). Beban = jumlah skripsi yang pernah dibimbing di repositori.")

# ---------- Input ----------
st.session_state.setdefault("query", "")
st.session_state.setdefault("dicari", False)
st.session_state.setdefault("topik", [])

tab_judul, tab_topik = st.tabs(["✍️ Ide judul / kalimat", "🏷️ Pilih topik"])
with tab_judul:
    st.caption("Contoh (klik untuk mencoba):")
    pil = st.pills("Contoh", list(CONTOH), label_visibility="collapsed", key="pil_contoh")
    if pil:
        st.session_state["query"] = CONTOH[pil]
        st.session_state["dicari"] = True
        st.session_state["mode"] = "judul"
    with st.form("form_judul", border=False):
        st.text_area("Ide judul atau topik skripsi", key="query", height=90,
                     placeholder="contoh: klasifikasi citra penyakit daun menggunakan CNN, atau cukup: keamanan jaringan")
        if st.form_submit_button("Cari dosen", type="primary", use_container_width=True):
            st.session_state["dicari"] = True
            st.session_state["mode"] = "judul"
with tab_topik:
    st.caption("Pilih satu atau beberapa topik, tidak perlu menulis judul lengkap.")
    with st.form("form_topik", border=False):
        topik_dipilih = st.multiselect("Topik", daftar_topik(), key="topik", placeholder="Ketik atau pilih topik",
                                       label_visibility="collapsed")
        if st.form_submit_button("Cari dosen", type="primary", use_container_width=True):
            st.session_state["dicari"] = True
            st.session_state["mode"] = "topik"

mode = st.session_state.get("mode", "judul")
query = st.session_state["query"].strip() if mode == "judul" else ", ".join(st.session_state["topik"])


# ---------- Tampilan hasil ----------
def chip(teks, kelas=""):
    return f'<span class="chip {kelas}">{html.escape(teks)}</span>'


def warna_beban(rasio):
    return "#2ea043" if rasio < 0.6 else ("#d29922" if rasio < 1 else "#d1453b")


def tampilkan(rec, results, query, bersih_k, kolom_sempit=False):
    if not results:
        st.warning("Tidak ada dosen yang cocok. Coba kata kunci lain atau longgarkan filter.")
        return
    q_terms = set(preprocess(perluas(query)[0] if sinonim else query))
    top = results[0]["skor"] or 1.0
    for i, r in enumerate(results[:bersih_k], 1):
        with st.container(border=True):
            terpakai, kuota = (int(x) for x in r["beban"].split("/"))
            rasio = terpakai / max(kuota, 1)
            st.markdown(f'<span class="rank">{i}</span><span class="nama">{html.escape(r["nama"])}</span>'
                        f'<div class="sub">{html.escape(r["bidang"])}</div>', unsafe_allow_html=True)
            m1, m2 = st.columns(2)
            m1.markdown(f'<div class="lbl">Kecocokan ({r["skor"]:.2f}, {r["skor"] / top:.0%} dari tertinggi)</div>'
                        f'<div class="bar"><div style="width:{min(r["skor"] / top, 1) * 100:.0f}%;background:#2b5fd9"></div></div>',
                        unsafe_allow_html=True)
            m2.markdown(f'<div class="lbl">Beban bimbingan {r["beban"]}'
                        f'{" (melebihi kuota)" if terpakai > kuota else ""}</div>'
                        f'<div class="bar"><div style="width:{min(rasio, 1) * 100:.0f}%;background:{warna_beban(rasio)}"></div></div>',
                        unsafe_allow_html=True)
            if r["rumpun"]:
                st.markdown('<div class="lbl">Rumpun KBI</div>' + chip(r["rumpun"], "rumpun"), unsafe_allow_html=True)
            if r["pakar"]:
                chips = ""
                for t in (x.strip() for x in r["pakar"].split(",") if x.strip()):
                    cocok = bool(q_terms & set(preprocess(t)))
                    chips += chip(t, "cocok" if cocok else "")
                st.markdown('<div class="lbl">Bidang keahlian (hijau = cocok dengan pencarianmu)</div>' + chips,
                            unsafe_allow_html=True)
            ex = rec.explain(query, r["id"], expand=sinonim)
            if ex["kata_kunci"]:
                st.markdown('<div class="lbl">Kata kunci yang cocok (bentuk dasar)</div>' +
                            "".join(chip(t) for t in ex["kata_kunci"]), unsafe_allow_html=True)
            if ex["judul_pendukung"]:
                with st.expander(f"Judul pendukung ({len(ex['judul_pendukung'])})"):
                    for it in ex["judul_pendukung"]:
                        st.write(f"- ({it['sumber']}) {it['judul']}")
            st.link_button("Cari profil di satudata UNJ", SATUDATA, help=f"Di halaman itu, ketik nama: {r['nama']}")


def hasil_untuk(label_profil):
    rec = get_recommender(PROFIL[label_profil])
    semua = rec.recommend(query, model=model, k=24, load_weight=load_w, expand=sinonim)
    if f_prodi:
        semua = [r for r in semua if any(p in r["bidang"] for p in f_prodi)]
    if f_rumpun:
        semua = [r for r in semua if r["rumpun"] in f_rumpun]
    return rec, [r for r in semua if r["skor"] > 0]


if st.session_state["dicari"] and not query:
    st.info("Tulis ide judul, pilih contoh, atau pilih minimal satu topik.")
elif st.session_state["dicari"] and query:
    st.divider()
    if sinonim:
        tambahan = perluas(query)[1]
        if tambahan:
            st.caption("Sinonim yang ikut dicari: " + ", ".join(tambahan))
    if bandingkan:
        st.info(f"Mode perbandingan: query yang sama dihitung dari dua profil (model: {model}).")
        kiri, kanan = st.columns(2)
        for kolom, lbl in ((kiri, kiri_label), (kanan, kanan_label)):
            with kolom:
                st.subheader(lbl)
                rec, res = hasil_untuk(lbl)
                tampilkan(rec, res, query, k)
    else:
        st.subheader(f"Hasil ({model}, {profil_label.lower()})")
        rec, res = hasil_untuk(profil_label)
        tampilkan(rec, res, query, k)
    with st.expander("Cara membaca hasil"):
        st.markdown(
            "- **Kecocokan**: makin panjang batang makin cocok. Skor hanya bisa dibandingkan dalam satu pencarian.\n"
            "- **Beban bimbingan**: jumlah skripsi yang pernah dibimbing dibanding kuota (dari data dosen).\n"
            "- **Bidang keahlian**: dari data dosen; yang berwarna hijau memuat kata dari pencarianmu.\n"
            "- **Kata kunci**: kata dari query yang paling berkontribusi pada skor dosen tersebut "
            "(selalu dihitung dari kontribusi BM25, juga saat TF-IDF dipilih).\n"
            "- **Judul pendukung**: judul publikasi, skripsi, atau keahlian dosen yang memuat kata dari query.\n"
            "- Hasil adalah **saran awal**, bukan keputusan. Tetap konsultasikan dengan dosen dan prodi.")

st.divider()
st.caption("Data: judul publikasi (Scopus, Google Scholar, Garuda, SINTA), judul skripsi di repositori UNJ (tanpa nama mahasiswa), "
           "dan data dosen. Proyek mata kuliah Temu Kembali Informasi, Prodi Sistem dan Teknologi Informasi, UNJ.")
