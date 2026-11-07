import json
import random
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageFilter

random.seed(7)
np.random.seed(7)

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
SRC = ROOT / "invoices"
OUT = ROOT / "scanned"
OUT.mkdir(parents=True, exist_ok=True)

truth = json.loads((ROOT / "ground_truth.json").read_text())

for row in truth:
    with pymupdf.open(SRC / row["file"]) as doc:
        pix = doc[0].get_pixmap(dpi=150)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    angle = random.uniform(-2.5, 2.5)
    img = img.rotate(angle, expand=True, fillcolor=(255, 255, 255), resample=Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 1.0)))
    arr = np.asarray(img).astype(np.float32)
    arr += np.random.normal(0, random.uniform(5, 18), arr.shape)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(OUT / (Path(row["file"]).stem + ".png"))

print(f"Created {len(truth)} scanned images in {OUT}")