from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

INPUT_DIR = Path("plots_imp_vs_nopf_by_case")
OUTPUT_DIR = Path("plots_imp_grouped_existing_all")
OUTPUT_DIR.mkdir(exist_ok=True)

BENCHMARKS = [
    "simple_triad",
    "spmv",
    "bfs",
    "merge",
    "quick",
    "matmult",
]

CONDITIONS = [
    ("l1d", "ddr4_1x", "L1D + DDR4 1x"),
    ("l1d", "ddr4_2x", "L1D + DDR4 2x"),
    ("l2", "ddr4_1x", "L2 + DDR4 1x"),
    ("l2", "ddr4_2x", "L2 + DDR4 2x"),
]

# We want the all-config PNGs, not top-N PNGs.
SUFFIX = "all_speedup_vs_nopf.png"

# Layout: 2 rows x 3 columns = 6 benchmark plots.
NROWS = 2
NCOLS = 3

TITLE_H = 90
PADDING = 24
GAP = 24
BG = "white"


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]

    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass

    return ImageFont.load_default()


title_font = load_font(44, bold=True)
subtitle_font = load_font(24, bold=False)


def find_png(benchmark, pf_level, memory):
    expected = INPUT_DIR / f"{benchmark}_{pf_level}_{memory}_{SUFFIX}"
    if expected.exists():
        return expected

    # Fallback: tolerate slightly different names.
    matches = list(INPUT_DIR.glob(f"{benchmark}_{pf_level}_{memory}_*all*speedup*vs*nopf*.png"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"Could not find PNG for {benchmark}, {pf_level}, {memory}")


def resize_keep_aspect(img, target_w):
    w, h = img.size
    if w == target_w:
        return img
    new_h = int(h * (target_w / w))
    return img.resize((target_w, new_h), Image.LANCZOS)


for pf_level, memory, condition_title in CONDITIONS:
    paths = [find_png(b, pf_level, memory) for b in BENCHMARKS]
    images = [Image.open(p).convert("RGB") for p in paths]

    # Normalize all images to same width for clean columns.
    # Use the minimum width to avoid huge output images.
    target_w = min(img.size[0] for img in images)
    images = [resize_keep_aspect(img, target_w) for img in images]

    cell_w = target_w
    cell_h = max(img.size[1] for img in images)

    canvas_w = PADDING * 2 + NCOLS * cell_w + (NCOLS - 1) * GAP
    canvas_h = TITLE_H + PADDING * 2 + NROWS * cell_h + (NROWS - 1) * GAP

    canvas = Image.new("RGB", (canvas_w, canvas_h), BG)
    draw = ImageDraw.Draw(canvas)

    title = f"IMP all-configuration speedup vs no-prefetch baseline"
    subtitle = condition_title

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)

    title_x = (canvas_w - (title_bbox[2] - title_bbox[0])) // 2
    subtitle_x = (canvas_w - (subtitle_bbox[2] - subtitle_bbox[0])) // 2

    draw.text((title_x, 15), title, fill="black", font=title_font)
    draw.text((subtitle_x, 62), subtitle, fill="black", font=subtitle_font)

    y0 = TITLE_H + PADDING

    for idx, img in enumerate(images):
        row = idx // NCOLS
        col = idx % NCOLS

        x = PADDING + col * (cell_w + GAP)
        y = y0 + row * (cell_h + GAP)

        # Top-align within each cell.
        canvas.paste(img, (x, y))

    out_path = OUTPUT_DIR / f"group_existing_all_{pf_level}_{memory}.png"
    canvas.save(out_path, quality=95)
    print(f"Wrote {out_path}")

print(f"Done. Grouped PNGs are in: {OUTPUT_DIR}")