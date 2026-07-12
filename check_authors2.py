import re
with open("test_output.html", "r", encoding="utf-8") as f:
    html = f.read()

# Authors div
authors_div = re.search(r'<div class="authors">(.*?)</div>', html, re.DOTALL)
if authors_div:
    content = authors_div.group(1).strip()
    print(f"Authors div content length: {len(content)}")
    print(f"Authors div: '{content[:300]}'")
    if content:
        print("AUTHORS ARE POPULATED!")
    else:
        print("Authors div is still EMPTY")

# Check for specific patterns
for pat in ['Author A', 'Author B', 'author-name', 'Department of']:
    if pat in html:
        print(f"Found '{pat}' in HTML")

# Check the full HTML title, abstract, keywords
title = re.search(r'<h1>(.*?)</h1>', html)
print(f"\nTitle: {title.group(1)[:100] if title else 'NOT FOUND'}")

abstract = re.search(r'abstract-label">.*?<p>(.*?)</p>', html, re.DOTALL)
if abstract:
    ab = re.sub(r'<[^>]+>', '', abstract.group(1)).strip()
    print(f"Abstract: {ab[:100]}... ({len(ab)} chars)")
    print(f"Abstract ends with period: {ab[-1] == '.'}")

# Chain of thought check
pre = html[:min(2000, html.lower().find('abstract'))] if 'abstract' in html.lower() else html[:500]
for indicator in ['thinking', 'reasoning', 'chain-of-thought', "i'll write", "let me"]:
    if indicator in pre.lower():
        print(f"WARNING: Found '{indicator}' in preamble")

print("\n--- ALL CHECKS DONE ---")
