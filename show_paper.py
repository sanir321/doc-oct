import requests, json

BASE = "https://backend-production-a605.up.railway.app"

# Upload
with open("test_hello.txt", "w") as f:
    f.write("Deep learning for medical image classification using convolutional neural networks and transfer learning.")
with open("test_hello.txt", "rb") as f:
    r = requests.post(f"{BASE}/api/upload", files={"file": ("paper.txt", f, "text/plain")}, timeout=15)
sid = r.json()["session_id"]

# Set mode (ieee)
r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "ieee"}, timeout=60)
data = r.json()

# Answer the first question
if data.get("question"):
    r = requests.post(f"{BASE}/api/answer-paper/{sid}", json={
        "question": data["question"],
        "answer": "Deep learning for medical image classification"
    }, timeout=60)
    data = r.json()

# Generate paper
r = requests.get(f"{BASE}/api/generate-paper-stream/{sid}", stream=True, timeout=180)
paper_text = ""
for line in r.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data: "):
        continue
    try:
        ev = json.loads(line[6:])
        if ev.get("type") == "done":
            paper_text = ev.get("result", {}).get("paper_text", "")
            break
    except Exception:
        pass

# Download HTML
r = requests.get(f"{BASE}/api/download-paper/{sid}/html", timeout=30)
with open("demo_paper.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print(f"Saved: demo_paper.html ({len(r.text)} bytes)")
