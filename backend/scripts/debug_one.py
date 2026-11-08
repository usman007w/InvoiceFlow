import json
import sys
from pathlib import Path

from app.extract.llm import extract_invoice
from app.extract.ocr import read_image_text

name = sys.argv[1]
ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
truth = json.loads((ROOT / "ground_truth.json").read_text())
row = next(r for r in truth if r["file"] == name)

text = read_image_text(ROOT / "scanned" / (Path(name).stem + ".png"))

print("--- OCR TEXT ---")
print(text)
print("--- EXPECTED ITEMS ---")
for it in row["invoice"]["line_items"]:
    print(it)
print("--- LLM ITEMS ---")
try:
    for it in extract_invoice(text).line_items:
        print(it.model_dump(mode="json"))
except Exception as e:
    print("ERROR", str(e)[:200])