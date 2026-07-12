"""Deep debug: trace why authors div is empty."""
import httpx, json, re

B = "https://backend-production-a605.up.railway.app"
TO = httpx.Timeout(120.0, connect=30.0)

# 1) Upload
with open("sample_test.txt", "rb") as f:
    r = httpx.post(f"{B}/api/upload", files={"file": ("sample_test.txt", f, "text/plain")}, timeout=TO)
print(f"Upload: {r.status_code}")
data = r.json()
sid = data["session_id"]
analysis = data.get("analysis", {})
print(f"analysis keys: {list(analysis.keys())}")
print(f"authors value: {repr(analysis.get('authors'))}")
print(f"domain value: {repr(analysis.get('domain'))}")

# 2) Answer the questions until ready
for attempt in range(5):
    r = httpx.post(f"{B}/api/ask/{sid}", timeout=TO)
    resp = r.json()
    if resp.get("ready"):
        print(f"Ready after {attempt+1} questions")
        break
    q = resp.get("question", "Do you have full content?")
    r2 = httpx.post(f"{B}/api/answer/{sid}", json={"question": q, "answer": "Yes, full content"}, timeout=TO)
    a_resp = r2.json()
    if a_resp.get("ready"):
        print(f"Ready after answer {attempt+1}")
        break

# 3) Generate
r = httpx.get(f"{B}/api/generate-stream/{sid}", timeout=TO)
print(f"\nGenerate: {r.status_code}, {len(r.text)} bytes")

# Parse SSE - find the 'done' event
for line in r.text.strip().split('\n'):
    if line.startswith('data: '):
        try:
            payload = json.loads(line[6:])
            if payload.get('type') == 'done':
                result = payload['result']
                html = result['html_content']
                paper = result['paper_text']
                latex = result['latex_content']
                
                # Check authors in html
                au_div = re.search(r'<div class="authors">(.*?)</div>', html, re.DOTALL)
                print(f"\nHTML authors div: '{au_div.group(1)[:200] if au_div else 'NOT FOUND'}'")
                
                # Check latex for authors
                au_latex = re.search(r'\\author\{([^}]*)\}', latex)
                print(f"LaTeX author block: '{au_latex.group(1)[:200] if au_latex else 'NOT FOUND'}'")
                
                # Check paper_text for author info
                first_200 = paper[:200]
                print(f"\nPaper text starts with:\n{first_200}")
                
                # Check if generate_ieee_html was even called properly
                if 'Author A' in html or 'Author' in html:
                    if au_div and au_div.group(1):
                        print("\nAUTHORS ARE IN THE DIV!")
                    else:
                        print("\n'Author' text found in HTML but NOT in the authors div!")
                else:
                    print("\n'Author' text NOT found anywhere in HTML")
                
                break
        except (json.JSONDecodeError, Exception) as e:
            pass
else:
    print("ERROR: No 'done' event found")
    print(f"Sample: {r.text[:500]}")
