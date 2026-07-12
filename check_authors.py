import re
with open("test_output.html", "r", encoding="utf-8") as f:
    html = f.read()

# Authors div
authors_div = re.search(r'<div class="authors">(.*?)</div>', html, re.DOTALL)
if authors_div:
    content = authors_div.group(1).strip()
    print(f"Authors div content: '{content[:200]}'")
    print(f"Authors div empty: {len(content) == 0}")

# Check the entire HTML - is there any author info anywhere?
print("\n--- Searching for author references ---")
author_lines = [i for i, line in enumerate(html.split('\n')) if 'author' in line.lower()]
for ln in author_lines:
    print(f"  Line {ln}: ...{html.split(chr(10))[ln][:100].strip()}...")

# What user answers were submitted? Check service code
print("\n--- Checking LLM response for author info ---")
# Read the raw generate output
print("\nDone. The authors div is empty, which means the HTML template/serializer"
      " is not extracting author data from the LLM output into the .authors div.")
