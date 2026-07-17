import fitz

print("=== OUR PDF - layout ===")
doc = fitz.open("demo_out/out/paper.pdf")
page = doc[0]
print(f"Page size: {page.rect.width:.0f}x{page.rect.height:.0f} pts")
blocks = page.get_text("dict")["blocks"]
for b in blocks:
    if b["type"] == 0:
        x0, y0, x1, y1 = b["bbox"]
        txt = "".join(s["text"] for l in b["lines"] for s in l["spans"])[:40].strip()
        if txt:
            print(f"  x0={x0:.0f} x1={x1:.0f} y0={y0:.0f}: {txt}")
doc.close()

print()
print("=== ACTUAL IEMT PDF - layout ===")
doc = fitz.open("IEMT2014-P054.pdf")
page = doc[0]
print(f"Page size: {page.rect.width:.0f}x{page.rect.height:.0f} pts")
blocks = page.get_text("dict")["blocks"]
for b in blocks:
    if b["type"] == 0:
        x0, y0, x1, y1 = b["bbox"]
        txt = "".join(s["text"] for l in b["lines"] for s in l["spans"])[:40].strip()
        if txt:
            print(f"  x0={x0:.0f} x1={x1:.0f} y0={y0:.0f}: {txt}")
doc.close()
