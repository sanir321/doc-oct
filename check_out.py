import os, sys, re
sys.path.insert(0, "backend")
from main import generate_ieee_html, generate_pdf_from_html, IEMT
from PIL import Image, ImageDraw

d = "demo_out"
import fitz
from pypdf import PdfReader

reader = PdfReader(f"{d}/out/paper.pdf")
with open(f"{d}/out/paper.pdf","rb") as f:
    ic = f.read().count(b'/Subtype /Image')
print(f"PDF: {os.path.getsize(f'{d}/out/paper.pdf'):,} bytes, {len(reader.pages)} pages, {ic} images")

doc = fitz.open(f"{d}/out/paper.pdf")
for i, page in enumerate(doc):
    blocks = page.get_text("dict")["blocks"]
    mid = page.rect.width/2
    print(f"\n=== Page {i+1} ===")
    for b in blocks:
        x0, y0, x1, y1 = b["bbox"]
        col = "R" if x0 > mid else "L"
        if b["type"] == 0:
            text = "".join(s["text"] for l in b["lines"] for s in l["spans"])[:70].strip()
            if text:
                print(f"  {col} y={y0:.0f}: {text}")
        elif b["type"] == 1:
            print(f"  {col} y={y0:.0f}-{y1:.0f}: IMAGE {x1-x0:.0f}x{y1-y0:.0f}")
doc.close()
