"""Deep debug v2: directly fetch HTML and LaTeX from download endpoint."""
import httpx, json, re

B = "https://backend-production-a605.up.railway.app"
TO = httpx.Timeout(120.0, connect=30.0)

with open("sample_test.txt", "rb") as f:
    r = httpx.post(f"{B}/api/upload", files={"file": ("sample_test.txt", f, "text/plain")}, timeout=TO)
sid = r.json()["session_id"]
print(f"Session: {sid}")

# Answer until ready
for _ in range(5):
    r = httpx.post(f"{B}/api/ask/{sid}", timeout=TO)
    resp = r.json()
    if resp.get("ready"):
        break
    q = resp.get("question", "Do you have full content?")
    r2 = httpx.post(f"{B}/api/answer/{sid}", json={"question": q, "answer": "Yes, full content"}, timeout=TO)
    if r2.json().get("ready"):
        break

# Generate
r = httpx.get(f"{B}/api/generate-stream/{sid}", timeout=TO)
print(f"Generate: {r.status_code}, {len(r.text)} bytes")

# Find done event
for line in r.text.strip().split('\n'):
    if line.startswith('data: '):
        try:
            payload = json.loads(line[6:])
            if payload.get('type') == 'done':
                result = payload['result']
                html_from_sse = result['html_content']
                latex_from_sse = result['latex_content']
                
                au_div = re.search(r'<div class="authors">(.*?)</div>', html_from_sse, re.DOTALL)
                print(f"\nHTML from SSE - authors div content:\n  '{au_div.group(1)[:300] if au_div else 'NOT FOUND'}'")
                break
        except Exception:
            pass

# Now fetch from download endpoint
r_html = httpx.get(f"{B}/api/download/{sid}/html", timeout=TO)
print(f"\nDownload HTML: {r_html.status_code}, {len(r_html.content)} bytes")

html_dl = r_html.text
au_div_dl = re.search(r'<div class="authors">(.*?)</div>', html_dl, re.DOTALL)
print(f"HTML from download - authors div content:\n  '{au_div_dl.group(1)[:300] if au_div_dl else 'NOT FOUND'}'")

# Check differences between SSE and download
print(f"\nHTML same?: {html_from_sse == html_dl}")

# Print the raw bytes of authors div area from download
idx = html_dl.find('authors">')
print(f"\nRaw HTML around authors div:\n{html_dl[idx-20:idx+200]}")

# Check LaTeX for author
au_latex = re.search(r'\\IEEEauthorblockN\{([^}]*)\}', latex_from_sse)
print(f"\nLaTeX authors: '{au_latex.group(1) if au_latex else 'NOT FOUND'}'")

# FULL inspection of generate_ieee_html template strings
print("\n--- Checking if authors variable is in template ---")
if '{authors_html}' in html_from_sse[:500]:
    print("FOUND: Template literal {authors_html} in output (not expanded!)")
else:
    print("OK: {authors_html} not found as literal (was expanded)")
