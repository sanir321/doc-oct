import fitz

doc = fitz.open("demo_out/out/paper.pdf")
page = doc[0]
print(f"Page: {page.rect.width:.0f}x{page.rect.height:.0f} pts\n")

blocks = page.get_text("dict")["blocks"]
for b in blocks:
    x0, y0, x1, y1 = b["bbox"]
    if b["type"] == 0:
        for l in b["lines"]:
            tx = l["bbox"][0]
            line_text = ""
            for s in l["spans"]:
                line_text += s["text"]
            line_text = line_text.strip()
            if line_text:
                mid = page.rect.width / 2
                col = "R" if tx > mid else "L"
                s = l["spans"][0]
                sz = s["size"]
                fn = s["font"]
                ly = l["bbox"][1]
                print(f'{col} y={ly:.0f} sz={sz:.1f} font={fn:15s} | {line_text[:80]}')
    elif b["type"] == 1:
        print(f"  y={y0:.0f}-{y1:.0f} w={x1-x0:.0f}h={y1-y0:.0f} | IMAGE")
doc.close()
