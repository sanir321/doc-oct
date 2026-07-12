import re, fitz
h = open("test_output.html").read()
secs = re.findall(r"<h2>(.*?)</h2>", h)
print("Sections:", secs)
am = re.search(r'abstract-label">(.*?)</span><p>(.*?)</p>', h, re.DOTALL)
if am:
    ab = re.sub(r"<[^>]+>", "", am.group(2)).strip()
    print("Abstract:", ab[:200])
km = re.search(r'kw-label">(.*?)</span>(.*?)</div>', h, re.DOTALL)
if km:
    kw = re.sub(r"<[^>]+>", "", km.group(2)).strip()
    print("Keywords:", kw)
doc = fitz.open("test_output.pdf")
print(f"\nPDF: {len(doc)} pages, {len(''.join(p.get_text() for p in doc))} chars")
for i, p in enumerate(doc):
    t = p.get_text()[:200]
    print(f"\n--- Page {i} ---\n{t}")
