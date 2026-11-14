import os
import pymupdf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

os.makedirs("img", exist_ok=True)
PDF_PATH = "../20751_Learning_Concept_Bottlen.pdf"

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"


def crop_between_texts(page, top_text, bottom_text, out_path, x_margin=40, pad_top=5, pad_bottom=5, dpi=300):
    """Wycina fragment strony PDF pomiędzy dwoma napisami (lub od góry strony, jeśli top_text=None)."""
    w, h = page.rect.width, page.rect.height
    y0 = 60
    if top_text:
        hits_top = page.search_for(top_text)
        if hits_top:
            y0 = hits_top[0].y1 + pad_top

    y1 = h - 60
    if bottom_text:
        hits_bot = page.search_for(bottom_text)
        if hits_bot:
            y1 = hits_bot[0].y0 - pad_bottom

    rect = pymupdf.Rect(x_margin, max(0, y0), w - x_margin, min(h, y1))
    pix = page.get_pixmap(clip=rect, dpi=dpi)
    pix.save(out_path)
    print(f"[PDF -> PNG] Zapisano: {out_path}")


if not os.path.exists(PDF_PATH):
    raise FileNotFoundError(
        f"Nie znaleziono pliku '{PDF_PATH}' w bieżącym folderze! "
        "Umieść plik PDF z artykułem w tym samym katalogu co skrypt."
    )

doc = pymupdf.open(PDF_PATH)

# 1. SLAJD 2: Zdjęcia ptaków i wyjaśnienia lokalne z CUB (strona 22 / indeks 21 - Dzięcioł i Dzierzba)
page_cub_expl = doc[21]
crop_between_texts(
    page_cub_expl,
    top_text="(d) Correctly predicted Arctic Tern",
    bottom_text="Figure 11:",
    out_path="img/slajd02_ptak.png",
    x_margin=55,
    pad_top=8,
    pad_bottom=4,
)

# 2. SLAJD 4: Wyciek informacji - losowe słowa ("bird balsamy", "bird punditic") ze zdjęciami ptaków (strona 17 / indeks 16)
page_leak = doc[16]
crop_between_texts(
    page_leak,
    top_text=None,
    bottom_text="Figure 7:",
    out_path="img/slajd04_leakage.png",
    x_margin=65,
    pad_bottom=5,
)

# 3. SLAJD 5: Schemat 4 kroków M-CBM (strona 3 / indeks 2 - Rysunek 1)
page_pipe = doc[2]
crop_between_texts(
    page_pipe,
    top_text=None,
    bottom_text="Figure 1:",
    out_path="img/slajd05_pipeline.png",
    x_margin=40,
    pad_bottom=5,
)

# 4. SLAJD 6: Zdjęcia ptaków z nałożonymi mapami aktywacji SAE (strona 29 / indeks 28 - Rysunek 15)
page_sae_birds = doc[28]
crop_between_texts(
    page_sae_birds,
    top_text="was looking.",
    bottom_text="(k) Green back",
    out_path="img/slajd06_sae_ptaki.png",
    x_margin=40,
    pad_top=10,
    pad_bottom=15,
)

# 5. SLAJD 9: Zdjęcie znamienia i błędna predykcja naprawiona jedną cechą (strona 23 / indeks 22 - Rysunek 12a/b)
page_isic = doc[22]
crop_between_texts(
    page_isic,
    top_text=None,
    bottom_text="(b) Melanocytic nevus wrongly predicted as Melanoma.",
    out_path="img/slajd09_isic.png",
    x_margin=50,
    pad_bottom=2,
)

# 6. SLAJD 10: Siatka zdjęć ptaków ze zbioru CUB-200-2011 dla cech (strona 19 / indeks 18 - Rysunek 8)
page_cub_grid = doc[18]
crop_between_texts(
    page_cub_grid,
    top_text=None,
    bottom_text="(k) Reddish-brown throat patch",
    out_path="img/slajd10_cub_grid.png",
    x_margin=40,
    pad_bottom=15,
)

doc.close()

# -------------------------------------------------------------------------
# CZĘŚĆ 2: Generowanie czystych diagramów i wykresów po polsku (Matplotlib)
# -------------------------------------------------------------------------

# SLAJD 2: Schemat problemu czarnej skrzynki (Black-Box)
fig, ax = plt.subplots(figsize=(8.5, 2.3), dpi=300)
ax.axis("off")
ax.set_xlim(0, 10)
ax.set_ylim(1.3, 4.1)

boxes_bb = [
    (0.5, 1.8, 2.2, 1.8, "#e9ecef", "#2b2f33", "Zdjęcie\nwejściowe\n(piksele RGB)"),
    (3.4, 1.8, 3.2, 1.8, "#3d405b", "white", "Głęboka sieć neuronowa\n(ResNet-18)\n[512 gęstych cech float]"),
    (7.3, 1.8, 2.2, 1.8, "#2a9d8f", "white", "Predykcja klasy:\nLasówka kapturkowa\n(p = 98.4%)"),
]
for x, y, bw, bh, bg_col, text_col, txt in boxes_bb:
    ax.add_patch(mpatches.FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=0.15", facecolor=bg_col, edgecolor="none"))
    ax.text(x + bw / 2, y + bh / 2, txt, ha="center", va="center", fontsize=9.5, fontweight="bold", color=text_col)

ax.annotate("", xy=(3.3, 2.7), xytext=(2.8, 2.7), arrowprops=dict(arrowstyle="->", lw=2.2, color="#4a6572"))
ax.annotate("", xy=(7.2, 2.7), xytext=(6.7, 2.7), arrowprops=dict(arrowstyle="->", lw=2.2, color="#4a6572"))

plt.tight_layout()
plt.savefig("img/slajd02_black_box.png", dpi=300, bbox_inches="tight")
plt.close()
print("[Diagram -> PNG] Zapisano: img/slajd02_black_box.png")


# SLAJD 3: Schemat modelu z wąskim gardłem cech (Concept Bottleneck Model)
fig, ax = plt.subplots(figsize=(8.8, 3.8), dpi=300)
ax.axis("off")
ax.set_xlim(0, 10)
ax.set_ylim(0.9, 5.0)

boxes_cbm = [
    (0.3, 1.8, 1.8, 2.4, "#e9ecef", "#2b2f33", "Zdjęcie\nwejściowe\n(RGB)"),
    (2.6, 1.8, 2.1, 2.4, "#457b9d", "white", "Ekstraktor cech\n(Backbone)\n512 wymiarów"),
    (5.2, 1.2, 2.4, 3.5, "#f4a261", "#222222", "Warstwa pojęć\n(CBL Bottleneck):\n\n[1] Żółta głowa\n[1] Czarna maska\n[0] Czerwony dziób\n[0] Białe paski"),
    (8.1, 1.8, 1.6, 2.4, "#2a9d8f", "white", "Klasyfikator\nliniowy\n\n-> Gatunek"),
]
for x, y, bw, bh, bg_col, text_col, txt in boxes_cbm:
    ax.add_patch(mpatches.FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=0.15", facecolor=bg_col, edgecolor="none"))
    ax.text(x + bw / 2, y + bh / 2, txt, ha="center", va="center", fontsize=9, fontweight="bold", color=text_col)

ax.annotate("", xy=(2.5, 3.0), xytext=(2.2, 3.0), arrowprops=dict(arrowstyle="->", lw=2, color="#4a6572"))
ax.annotate("", xy=(5.1, 3.0), xytext=(4.8, 3.0), arrowprops=dict(arrowstyle="->", lw=2, color="#4a6572"))
ax.annotate("", xy=(8.0, 3.0), xytext=(7.7, 3.0), arrowprops=dict(arrowstyle="->", lw=2, color="#4a6572"))

plt.tight_layout()
plt.savefig("img/slajd03_cbm_schemat.png", dpi=300, bbox_inches="tight")
plt.close()
print("[Diagram -> PNG] Zapisano: img/slajd03_cbm_schemat.png")


# SLAJD 7: Wykres wkładu cech dla Lasówki kapturkowej (M-CBM)
concepts_bird = [
    "Suma pozostałych 273 cech",
    "Oliwkowozielony grzbiet",
    "Żółty wierzch, ciemne ciało i dziób",
    "Jaskrawożółte pióra z czarną czapką",
    "Czarna maska wokół żółtej twarzy",
    "Żółty ptak z czarną maską wokół oczu",
]
scores_bird = [0.05, 0.12, 0.38, 1.28, 4.34, 4.80]

fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=300)
bars = ax.barh(
    concepts_bird,
    scores_bird,
    color=["#999999", "#2a9d8f", "#2a9d8f", "#2a9d8f", "#e63946", "#e63946"],
    height=0.6,
)
ax.set_xlabel("Wkład cechy do decyzji (aktywacja × waga klasyfikatora)", fontsize=10.5, fontweight="bold")
fig.suptitle("Decyzja M-CBM dla Lasówki kapturkowej (5 kluczowych cech)", fontsize=12, fontweight="bold", y=0.98)
ax.set_xlim(0, 5.7)
ax.grid(axis="x", linestyle="--", alpha=0.5)

for bar in bars:
    w = bar.get_width()
    ax.annotate(
        f"+{w:.2f}",
        xy=(w, bar.get_y() + bar.get_height() / 2),
        xytext=(5, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=9.5,
        fontweight="bold",
    )

plt.tight_layout(rect=[0, 0, 1, 0.93])
plt.savefig("img/slajd07_wyjasnienie_ptak.png", dpi=300, bbox_inches="tight", pad_inches=0.15)
plt.close()
print("[Wykres -> PNG] Zapisano: img/slajd07_wyjasnienie_ptak.png")

print("\nWszystkie niezbędne grafiki zaktualizowane w folderze 'img/'!")
