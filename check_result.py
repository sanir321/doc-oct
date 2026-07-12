import re, fitz

# --- HTML ---
h = open("test_output.html").read()

# Body
bm = re.search(r"<body>(.*?)</body>", h, re.DOTALL)
body = bm.group(1) if bm else h

# Title
tm = re.search(r"<h1>(.*?)</h1>", h)
print("TITLE:", tm.group(1) if tm else "N/A")

# Authors
am = re.search(r'<div class="authors">(.*?)</div>', h, re.DOTALL)
if am:
    print("AUTHORS:", am.group(1)[:200])

# Abstract
abm = re.search(r'abstract-label">(.*?)</span><p>(.*?)</p>', h, re.DOTALL)
if abm:
    ab = re.sub(r"<[^>]+>", "", abm.group(2)).strip()
    print("ABSTRACT:", ab[:200])
    print("  Has co't (bad):", "wants me" in ab.lower() or "write a" in ab.lower()[:20])

# Sections
secs = re.findall(r"<h2>(.*?)</h2>", h)
print(f"SECTIONS ({len(secs)}):", secs)

# References
refm = re.search(r'class="references">(.*?)(</div>|$)', h, re.DOTALL)
if refm:
    refs = re.findall(r"\[(\d+)\]", refm.group(1))
    print(f"REFERENCES: {len(refs)} found")

# Tables
tables = re.findall(r"<table>", h)
print(f"TABLES: {len(tables)}")

# --- PDF ---
doc = fitz.open("test_output.pdf")
txt = "".join(p.get_text() for p in doc)
print(f"\nPDF: {len(doc)} pages, {len(txt)} chars")
print(f"  Valid: {open('test_output.pdf','rb').read()[:5] == b'%PDF-'}")
print(f"  Has co't (bad): {'wants me' in txt.lower()}")
print(f"  Has Abstract: {'Abstract' in txt}")
print(f"  Has References: {'References' in txt}")
print(f"  Has tables (|): {txt.count('|')} pipes")
