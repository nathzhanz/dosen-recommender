"""Membuat grafik perbandingan 4 konfigurasi dari eval/hasil_evaluasi.csv.

Jalankan:  python -m src.plot_evaluasi
Hasil:     eval/grafik_evaluasi.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "eval"
df = pd.read_csv(OUT / "hasil_evaluasi.csv")
df["label"] = df["profil"].str.capitalize() + "\n" + df["model"]

metrik = ["Success@1", "Success@3", "MRR"]
warna = ["#4c72b0", "#f28e2b", "#59a14f"]
lebar = 0.26

fig, ax = plt.subplots(figsize=(8, 4.2))
for i, (m, w) in enumerate(zip(metrik, warna)):
    xs = [x + (i - 1) * lebar for x in range(len(df))]
    batang = ax.bar(xs, df[m], lebar, label=m, color=w)
    for b, v in zip(batang, df[m]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v:.2f}",
                ha="center", fontsize=8)

ax.set_xticks(range(len(df)))
ax.set_xticklabels(df["label"])
ax.set_ylabel("Nilai metrik")
ax.set_ylim(0, max(df[metrik].max()) + 0.1)
ax.legend(ncol=3, frameon=False, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "grafik_evaluasi.png", dpi=200)
print("Tersimpan:", OUT / "grafik_evaluasi.png")
