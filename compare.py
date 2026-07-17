import fitz

print("=" * 70)
print("OUR PDF")
print("=" * 70)
doc = fitz.open("demo_out/out/paper.pdf")
page = doc[0]
mid = page.rect.width / 2
blocks = page.get_text("dict")["blocks"]
for b in blocks:
    x0, y0 = b["bbox"][0], b["bbox"][1]
    col = "R" if x0 > mid else "L"
    if b["type"] == 0:
        for l in b["lines"]:
            line_text = "".join(s["text"] for s in l["spans"]).strip()
            if line_text:
                s = l["spans"][0]
                print(f'{col} y={l["bbox"][1]:.0f} sz={s["size"]:.1f} {s["font"]:15s} | {line_text[:80]}')
    elif b["type"] == 1:
        print(f'{col} y={y0:.0f}-{b["bbox"][3]:.0f} | IMAGE')
doc.close()

print()
print("=" * 70)
print("ACTUAL IEMT 2014 - Page 1")
print("=" * 70)
doc = fitz.open("IEMT2014-P054.pdf")
page = doc[0]
mid = page.rect.width / 2
blocks = page.get_text("dict")["blocks"]
for b in blocks:
    x0, y0 = b["bbox"][0], b["bbox"][1]
    col = "R" if x0 > mid else "L"
    if b["type"] == 0:
        for l in b["lines"]:
            line_text = "".join(s["text"] for s in l["spans"]).strip()
            if line_text:
                s = l["spans"][0]
                print(f'{col} y={l["bbox"][1]:.0f} sz={s["size"]:.1f} {s["font"]:15s} | {line_text[:80]}')
    elif b["type"] == 1:
        print(f'{col} y={y0:.0f}-{b["bbox"][3]:.0f} | IMAGE')
doc.close()
