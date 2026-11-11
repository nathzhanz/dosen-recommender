"""Ambil judul skripsi + dosen pembimbing dari repository.unj.ac.id (EPrints) - jalankan di laptop.

Etika & aturan:
- Hanya membuka halaman publik (daftar per prodi/tahun dan halaman rekaman skripsi), TIDAK /cgi/*.
- Mengecek robots.txt, memakai jeda antar permintaan, dan menyimpan cache HTML agar tidak mengulang.
- NAMA MAHASISWA TIDAK DISIMPAN. Yang disimpan hanya: id rekaman, judul, tahun, prodi, pembimbing.

Pemakaian:
  python data_collection/collect_unj.py                       # default: S1 Sistem dan TI
  python data_collection/collect_unj.py --divisions S1_Sistem_dan_TI S1_Ilmu_Komputer
  python data_collection/collect_unj.py --debug 58128         # simpan HTML mentah 1 rekaman untuk cek parser
Hasil: data_collection/out/theses_raw.csv
"""
import argparse
import csv
import re
import time
import urllib.robotparser
from html import unescape
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://repository.unj.ac.id"
UA = "TKI-UNJ-student-project/1.0 (tugas kuliah; kontak: isi-email-kelompok)"  # GANTI dengan email kelompokmu
OUT = Path(__file__).parent / "out"
CACHE = OUT / "cache"
DELAY = 2.0

DEG = r"(?:S\.?\s?Kom|M\.?\s?Kom|M\.?\s?Cs|M\.?\s?T|S\.?\s?T|M\.?\s?Sc|M\.?\s?Eng|M\.?\s?Si|Ph\.?\s?D|S\.?\s?Si|M\.?\s?Pd|S\.?\s?Pd|M\.?\s?M|M\.?\s?Ak|S\.?\s?E|M\.?\s?E|S\.?\s?Pi)"
NAME_RE = re.compile(
    r"((?:Dr\.|Prof\.|Ir\.)?\s*[A-Z][\w'’.\-]*(?:\s+[A-Z][\w'’.\-]*){0,4}(?:\s*,\s*" + DEG + r"\.?)+)")
PREFIX_RE = re.compile(r"^(?:Dosen Pembimbing|Pembimbing|Contributors|Additional Information|Divisions)\s*:?\s*", re.I)

rp = urllib.robotparser.RobotFileParser()


def init_robots():
    rp.set_url(BASE + "/robots.txt")
    try:
        rp.read()
    except Exception:
        print("peringatan: robots.txt tidak terbaca, tetap hati-hati dan pelan-pelan")


def fetch(url: str) -> str:
    key = re.sub(r"[^A-Za-z0-9]+", "_", url)[-150:] + ".html"
    f = CACHE / key
    if f.exists():
        return f.read_text(encoding="utf-8", errors="ignore")
    if rp.last_checked:
        if not rp.can_fetch(UA, url):
            raise PermissionError(f"robots.txt melarang: {url}")
    time.sleep(DELAY)
    req = Request(url, headers={"User-Agent": UA})
    html = urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(html, encoding="utf-8")
    return html


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def division_url(div: str) -> str:
    # EPrints meng-encode '_' menjadi '=5F' pada URL view
    return f"{BASE}/view/divisions/{div.replace('_', '=5F')}/"


def list_years(div: str) -> list[str]:
    html = fetch(division_url(div))
    return sorted(set(re.findall(r'href="(?:[^"]*/)?(\d{4})\.html"', html)))


def list_records(div: str, year: str) -> list[str]:
    html = fetch(f"{division_url(div)}{year}.html")
    ids = re.findall(r'href="https?://repository\.unj\.ac\.id/(\d+)/"', html)
    ids += re.findall(r'href="/(\d+)/"', html)
    return sorted(set(ids), key=int)


def meta(html: str, name: str) -> list[str]:
    pat = r'<meta\s+name="%s"\s+content="([^"]*)"' % re.escape(name)
    return [unescape(x).strip() for x in re.findall(pat, html, flags=re.I)]


def parse_record(html: str) -> dict:
    title = (meta(html, "eprints.title") or meta(html, "DC.title") or [""])[0]
    if not title:
        m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
        title = strip_tags(m.group(1)) if m else ""
    year = ""
    for d in meta(html, "eprints.date") + meta(html, "DC.date"):
        m = re.match(r"(\d{4})", d)
        if m:
            year = m.group(1); break

    advisors = []
    # 1) meta kontributor (tidak menyimpan creator/mahasiswa)
    advisors += meta(html, "eprints.contributors_name") + meta(html, "DC.contributor")
    # 2) baris tabel "Contributors" / "Additional Information" pada halaman
    text = strip_tags(html)
    for label in ("Contributors", "Additional Information", "Dosen Pembimbing", "Pembimbing"):
        m = re.search(label + r"\s*:?\s*(.{0,400})", text)
        if m:
            advisors += [PREFIX_RE.sub("", n.strip()) for n in NAME_RE.findall(m.group(1))]
    clean, seen = [], set()
    for a in advisors:
        a = re.sub(r"\s+", " ", a).strip(" ,;.")
        a = re.sub(r"\s*(THS|Thesis advisor|Dosen Pembimbing).*$", "", a, flags=re.I)
        key = re.sub(r"[^a-z]", "", a.lower())
        if len(key) > 4 and key not in seen:
            seen.add(key); clean.append(a)
    div = ""
    m = re.search(r"(S1[ _][A-Za-z_ ]+|S2[ _][A-Za-z_ ]+)", strip_tags(html))
    if m:
        div = m.group(1).strip()
    return {"judul": title, "tahun": year, "prodi": div, "pembimbing": " | ".join(clean)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--divisions", nargs="+", default=["S1_Sistem_dan_TI"])
    ap.add_argument("--years", nargs="*", help="batasi tahun, contoh: 2024 2025 2026")
    ap.add_argument("--debug", help="id rekaman: simpan HTML mentah ke out/debug_<id>.html lalu berhenti")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    init_robots()

    if args.debug:
        html = fetch(f"{BASE}/{args.debug}/")
        (OUT / f"debug_{args.debug}.html").write_text(html, encoding="utf-8")
        print(parse_record(html)); return

    rows = []
    for div in args.divisions:
        years = args.years or list_years(div)
        print(f"{div}: tahun {years}")
        for y in years:
            for rid in list_records(div, y):
                try:
                    rec = parse_record(fetch(f"{BASE}/{rid}/"))
                except Exception as e:
                    print("  lewati", rid, e); continue
                rec.update({"eprint_id": rid, "tahun": rec["tahun"] or y})
                rec["prodi"] = rec["prodi"] or div
                rows.append(rec)
                print(f"  {rid} | {rec['tahun']} | {rec['pembimbing'] or '(PEMBIMBING TIDAK TERBACA)'} | {rec['judul'][:60]}")
    cols = ["eprint_id", "judul", "tahun", "prodi", "pembimbing"]
    with open(OUT / "theses_raw.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows({c: r[c] for c in cols} for r in rows)
    empty = sum(1 for r in rows if not r["pembimbing"])
    print(f"\nselesai: {len(rows)} skripsi, {empty} tanpa pembimbing terbaca -> {OUT/'theses_raw.csv'}")
    if empty:
        print("Kalau banyak yang kosong, jalankan: python data_collection/collect_unj.py --debug <id> dan kirim hasil/ HTML-nya ke Claude.")


if __name__ == "__main__":
    main()
