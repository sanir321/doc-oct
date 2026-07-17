import requests, json, os

BASE = "https://backend-production-a605.up.railway.app"

with open("_t.txt", "w") as f:
    f.write("Deep learning for medical image classification using CNNs and transfer learning.")
with open("_t.txt", "rb") as f:
    r = requests.post(f"{BASE}/api/upload", files={"file": ("p.txt", f, "text/plain")}, timeout=15)
sid = r.json()["session_id"]

r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "ieee"}, timeout=60)
data = r.json()

if data.get("question"):
    r = requests.post(f"{BASE}/api/answer-paper/{sid}",
        json={"question": data["question"], "answer": "yes"}, timeout=60)

r = requests.get(f"{BASE}/api/generate-paper-stream/{sid}", stream=True, timeout=180)
for line in r.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data: "):
        continue
    try:
        ev = json.loads(line[6:])
        if ev.get("type") == "done":
            break
    except Exception:
        pass

r = requests.get(f"{BASE}/api/download-paper/{sid}/pdf?format=iemt", timeout=60)
with open("demo_paper.pdf", "wb") as f:
    f.write(r.content)
print(f"Saved: demo_paper.pdf ({len(r.content):,} bytes)")
os.remove("_t.txt")
