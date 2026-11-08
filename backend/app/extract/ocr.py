import os
from pathlib import Path

import pytesseract
from PIL import Image

_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
_cmd = os.getenv("TESSERACT_CMD", _default)
if Path(_cmd).exists():
    pytesseract.pytesseract.tesseract_cmd = _cmd


def read_image_text(path):
    with Image.open(path) as img:
        return pytesseract.image_to_string(img.convert("L"))