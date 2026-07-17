import requests, json, os

BASE = "https://backend-production-a605.up.railway.app"

doc = (
    "Professional Summary: Experienced software engineer with 5 years in full-stack development.\n"
    "Skills: Python, JavaScript, React, Node.js, PostgreSQL, Docker, AWS.\n"
    "Work Experience: Senior Developer at TechCorp (2021-2025). Built microservices and REST APIs.\n"
    "Education: B.Tech in Computer Science, IIT Bombay (2016-2020).\n"
    "Projects: Built an e-commerce platform with 10k+ daily users."
)

with open("_tr.txt", "w") as f:
    f.write(doc)
with open("_tr.txt", "rb") as f:
    r = requests.post(f"{BASE}/api/upload", files={"file": ("resume.txt", f, "text/plain")}, timeout=15)
sid = r.json()["session_id"]

r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "resume"}, timeout=60)
data = r.json()

for i in range(8):
    if not data.get("question"):
        break
    q, qtype = data["question"], data.get("type", "")
    if qtype in ("name_confirm", "email_confirm"):
        ans = "Yes, that's correct"
    elif qtype == "name":
        ans = "Samir Khadka"
    elif qtype == "email":
        ans = "samir@example.com"
    elif qtype == "phone":
        ans = "+1-555-1234"
    else:
        ans = "No more details"
    r = requests.post(f"{BASE}/api/answer-resume/{sid}", json={"question": q, "answer": ans}, timeout=60)
    data = r.json()
    if data.get("ready"):
        break

r = requests.get(f"{BASE}/api/generate-resume-stream/{sid}", stream=True, timeout=180)
html_content = ""
for line in r.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data: "):
        continue
    try:
        ev = json.loads(line[6:])
        if ev.get("type") == "done":
            html_content = ev["result"]["resume_html"]
            break
    except Exception:
        pass

out_path = "demo_resume.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Saved: {out_path} ({len(html_content)} bytes)")
os.remove("_tr.txt")
