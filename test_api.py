import httpx, json, time

BASE = "https://backend-production-a605.up.railway.app"
TO = httpx.Timeout(120.0, connect=30.0)

with open("sample_test.txt", "rb") as f:
    resp = httpx.post(f"{BASE}/api/upload", files={"file": ("sample_test.txt", f, "text/plain")}, timeout=TO)
print("1. Upload:", resp.status_code)
if resp.status_code != 200:
    print(resp.text[:500])
    exit()
data = resp.json()
session_id = data["session_id"]
print(f"Session: {session_id}")

ready = data.get("ready") or data.get("analysis", {}).get("ready", False)
question = data.get("question")

for i in range(10):
    if ready:
        print(f"Ready! round {i}")
        break

    q_text = ""
    opts = []
    if question:
        q_text = question.get("question", "")
        opts = question.get("options", [])
        print(f"Q: {q_text[:80]}")
        answer = opts[0] if opts else "This is a comprehensive NLP review covering ML techniques."
        resp = httpx.post(f"{BASE}/api/answer/{session_id}",
            json={"question": q_text, "answer": answer}, timeout=TO)
        print(f"  Answer {i}: {resp.status_code}")
        try:
            rd = resp.json()
            print(f"  Response: {json.dumps(rd)[:200]}")
        except:
            print(f"  Raw: {resp.text[:200]}")
            break
        if isinstance(rd, dict):
            if rd.get("ready") or rd.get("needs_clarification"):
                ready = True
            question = rd
        else:
            ready = True
    else:
        resp = httpx.post(f"{BASE}/api/ask/{session_id}", timeout=TO)
        print(f"  Ask: {resp.text[:200]}")
        try:
            rd = resp.json()
            if rd.get("ready"):
                ready = True
            else:
                question = rd
        except:
            print(f"  Ask raw: {resp.text[:100]}")
            break

# Generate
print("\nGenerating...")
resp = httpx.get(f"{BASE}/api/generate-stream/{session_id}", timeout=TO)
print(f"Generate: {resp.status_code}, {len(resp.text)} chars")

# Download HTML
resp = httpx.get(f"{BASE}/api/download/{session_id}/html", timeout=TO)
print(f"\nHTML: {resp.status_code}, {len(resp.content)} bytes")
fn = "test_output.html"
with open(fn, "wb") as f: f.write(resp.content)
print(f"Saved {fn}")
print(resp.text[:600])

# Download PDF
resp = httpx.get(f"{BASE}/api/download/{session_id}/pdf", timeout=TO)
print(f"\nPDF: {resp.status_code}, {len(resp.content)} bytes")
fn2 = "test_output.pdf"
with open(fn2, "wb") as f: f.write(resp.content)
print(f"Saved {fn2}")
