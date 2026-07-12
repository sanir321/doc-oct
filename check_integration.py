"""Integration test result checker (no emojis)."""
import re
import os

# 1. Check HTML for sections, abstract, authors
with open("test_output.html", "r", encoding="utf-8") as f:
    h = f.read()

print("=" * 60)
print("HTML INSPECTION")
print("=" * 60)

# Sections
secs = re.findall(r"<h2>(.*?)</h2>", h)
print(f"\nSections ({len(secs)}): {secs}")

# Abstract
am = re.search(r'abstract-label">(.*?)</span><p>(.*?)</p>', h, re.DOTALL)
if am:
    ab = re.sub(r"<[^>]+>", "", am.group(2)).strip()
    print(f"\nAbstract ({len(ab)} chars):")
    print(f"  Start: {ab[:150]}...")
    print(f"  End:   ...{ab[-150:]}")
    if ab[-1] == ".":
        print("  STATUS: Complete sentence")
    else:
        print("  WARNING: Abstract may be cut off")
else:
    print("  WARNING: No abstract found")

# Keywords
km = re.search(r'kw-label">(.*?)</span>(.*?)</div>', h, re.DOTALL)
if km:
    kw = re.sub(r"<[^>]+>", "", km.group(2)).strip()
    print(f"\nKeywords: {kw}")

# Author info - dump all relevant HTML around author area
author_area = h[h.find('author'):h.find('author')+2000] if 'author' in h.lower() else h[:2000]
print(f"\nAuthor area HTML ({len(author_area)} chars):")
print(author_area[:800])

# Try various author patterns
aus1 = re.findall(r'email-author-label">(.*?)</span>', h)
aus2 = re.findall(r'<p class="text-gray-600[^"]*"[^>]*>(.*?)</p>', h)
aus3 = re.findall(r'author-name[^>]*>(.*?)<', h)
print(f"\nAuthors (email-author-label pattern): {len(aus1)}")
print(f"Authors (text-gray-600 pattern): {len(aus2)}")
print(f"Authors (author-name pattern): {len(aus3)}")

# Dump all p tags near author section
p_tags = re.findall(r'<p[^>]*>(.*?)</p>', h[1000:5000])
print(f"\nP-tags in content area: {len(p_tags)}")
for i, p in enumerate(p_tags[:10]):
    txt = re.sub(r"<[^>]+>", "", p).strip()
    if txt and len(txt) > 2:
        print(f"  P[{i}]: {txt[:120]}")

# Chain-of-thought check
pre_abstract = h[:h.lower().find("abstract-label")] if "abstract-label" in h.lower() else h[:500]
coot_indicators = ["thinking", "chain-of-thought", "i'll write", "let me", "first,", "step 1"]
found_coot = [w for w in coot_indicators if w in pre_abstract.lower()]
if found_coot:
    print(f"\nWARNING: Possible chain-of-thought indicators: {found_coot}")
else:
    print("\nNo chain-of-thought indicators detected before abstract")

print("\n" + "=" * 60)
print("PDF INSPECTION")
print("=" * 60)

with open("test_output.pdf", "rb") as f:
    header = f.read(5)
    print(f"\nPDF header: {header}")
    print(f"  Valid PDF: {header == b'%PDF-'}")

size = os.path.getsize("test_output.pdf")
print(f"  File size: {size} bytes")

try:
    import fitz
    doc = fitz.open("test_output.pdf")
    pages = len(doc)
    all_text = "".join(p.get_text() for p in doc)
    print(f"\nPyMuPDF: {pages} pages, {len(all_text)} total chars")
    print(f"  PDF starts: {all_text[:300]}")
    print(f"  PDF ends: {all_text[-200:]}")
    for i, p in enumerate(doc):
        t = p.get_text()
        print(f"\n--- Page {i} ({len(t)} chars) ---")
        print(t[:300])
    doc.close()
except ImportError:
    print("  PyMuPDF not available")
    
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"PDF valid: {header == b'%PDF-'}")
print(f"Sections: {len(secs)}")
print(f"Abstract: {len(ab) if am else 0} chars")
print(f"Chain-of-thought: {'DETECTED' if found_coot else 'none'}")
print(f"Authors count (email pattern): {len(aus1)}")
