"""Check the raw LLM generate-stream output."""
import httpx, json

B = "https://backend-production-a605.up.railway.app"
TO = httpx.Timeout(120.0, connect=30.0)

with open("sample_test.txt", "rb") as f:
    r = httpx.post(f"{B}/api/upload", files={"file": ("sample_test.txt", f, "text/plain")}, timeout=TO)
print(f"Upload: {r.status_code}")
data = r.json()
sid = data["session_id"]
print(f"Session: {sid}")
print(f"Authors in analysis: {data.get('analysis', {}).get('authors')}")

# Answer
r = httpx.post(f"{B}/api/answer/{sid}", json={"question": "Full paper sections", "answer": "Full paper sections"}, timeout=TO)
print(f"\nAnswer1: {r.status_code}, {r.text[:200]}")

# Get generate-stream
r = httpx.get(f"{B}/api/generate-stream/{sid}", timeout=TO)
print(f"\nGenerate: {r.status_code}, {len(r.text)} chars")

# Parse SSE to get the final 'done' event
lines = r.text.strip().split('\n')
for i, line in enumerate(lines):
    if line.startswith('data: '):
        try:
            payload = json.loads(line[6:])
            if payload.get('type') == 'done':
                result = payload.get('result', {})
                print(f"\n--- RESULT ---")
                print(f"paper_text length: {len(result.get('paper_text', ''))}")
                html = result.get('html_content', '')
                authors_div_start = html.find('<div class="authors">')
                authors_div_end = html.find('</div>', authors_div_start)
                print(f"authors div HTML: {html[authors_div_start:authors_div_end+6]}")
                print(f"latex length: {len(result.get('latex_content', ''))}")
                break
        except json.JSONDecodeError:
            pass
else:
    print("No 'done' event found in SSE response")
    # Print first 2000 chars of raw response
    print(f"\nRaw response preview:\n{r.text[:2000]}")
