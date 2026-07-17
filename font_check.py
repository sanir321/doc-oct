import fitz

print("=== OUR GENERATED PDF ===")
doc = fitz.open("demo_out/out/paper.pdf")
page = doc[0]
blocks = page.get_text("dict")["blocks"]
for b in blocks:
    if b["type"] == 0:
        for l in b["lines"]:
            for s in l["spans"]:
                txt = s["text"].strip()
                if txt:
                    size = s["size"]
                    font = s["font"]
                    y = l["bbox"][1]
                    print(f"  size={size:.1f} font={font} y={y:.0f}: {txt[:70]}")
doc.close()

print()
print("=== ACTUAL IEMT2014-P054 PDF ===")
doc = fitz.open("IEMT2014-P054.pdf")
page = doc[0]
blocks = page.get_text("dict")["blocks"]
for b in blocks:
    if b["type"] == 0:
        for l in b["lines"]:
            for s in l["spans"]:
                txt = s["text"].strip()
                if txt:
                    size = s["size"]
                    font = s["font"]
                    y = l["bbox"][1]
                    print(f"  size={size:.1f} font={font} y={y:.0f}: {txt[:70]}")
doc.close()
