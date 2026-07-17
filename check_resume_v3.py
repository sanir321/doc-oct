import requests, json, time

BASE = "https://backend-production-a605.up.railway.app"

with open("_t.txt", "w") as f:
    f.write("""John Smith
john.smith@email.com
+1 555-0123
LinkedIn: linkedin.com/in/johnsmith
GitHub: github.com/johnsmith
San Francisco, CA

EDUCATION
Bachelor of Science in Computer Science - Stanford University, 2020, GPA: 3.8
Master of Science in Machine Learning - MIT, 2022

EXPERIENCE
Senior Software Engineer at Google, Mountain View CA, 2022-2024
- Led a team of 5 engineers building ML-based recommendation systems serving 10M+ users
- Improved system latency by 40% through distributed caching and query optimization
- Designed and deployed microservices architecture using Python, Go, and Kubernetes
- Mentored 3 junior engineers through structured onboarding program

Machine Learning Engineer at Amazon, Seattle WA, 2020-2022
- Developed NLP pipelines for customer sentiment analysis processing 1M+ reviews daily
- Built real-time data processing system using Apache Spark and Kafka
- Reduced model inference time by 60% through quantization and model pruning

SKILLS
Languages: Python, Go, Java, TypeScript, SQL
Frameworks: PyTorch, TensorFlow, FastAPI, React, Spring Boot
Tools: Kubernetes, Docker, AWS, GCP, Apache Spark, Kafka, PostgreSQL, Redis

PROJECTS
Real-time Anomaly Detection System | Python, PyTorch, Kafka - Built streaming anomaly detection system processing 100K+ events/second. Reduced false positive rate by 35% using ensemble methods.

CERTIFICATIONS
AWS Solutions Architect Professional
Google Cloud Professional Data Engineer
""")

with open("_t.txt", "rb") as f:
    r = requests.post(f"{BASE}/api/upload", files={"file": ("resume.txt", f, "text/plain")}, timeout=30)
assert r.status_code == 200, r.text
sid = r.json()["session_id"]
print(f"Session: {sid}")

r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "resume"}, timeout=120)
data = r.json()
print(f"Set-mode: ready={data.get('ready')}, has_q={'question' in data}")

max_q = 10
while not data.get("ready") and data.get("question") and max_q > 0:
    q = data["question"]
    print(f"  Q: {q[:80]}...")
    r = requests.post(f"{BASE}/api/answer-resume/{sid}",
        json={"question": q, "answer": "yes"}, timeout=120)
    data = r.json()
    max_q -= 1

r = requests.get(f"{BASE}/api/generate-resume-stream/{sid}", stream=True, timeout=300)
full = ""
for line in r.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data: "):
        continue
    try:
        ev = json.loads(line[6:])
        t = ev.get("type")
        if t == "token":
            full += ev.get("content", "").replace("\\n", "\n").replace("\\r", "\r")
        elif t == "done":
            print("Result keys:", list(ev.get("result", {}).keys()))
            rd = ev.get("result", {}).get("resume_data", {})
            print(f"  name={rd.get('name')} email={rd.get('email')} linkedin={rd.get('linkedin')}")
            print(f"  education={len(rd.get('education',[]))} experience={len(rd.get('experience',[]))}")
            break
        elif t == "error":
            print("Stream error:", ev.get("message"))
            break
    except Exception as e:
        print(f"Parse error: {e}")
        continue

print(f"\nTotal chars: {len(full)}")

r = requests.get(f"{BASE}/api/download-resume/{sid}/html", timeout=60)
if r.status_code == 200:
    with open("resume_v3.html", "wb") as f:
        f.write(r.content)
    print(f"HTML: resume_v3.html ({len(r.content):,} bytes)")

r = requests.get(f"{BASE}/api/download-resume/{sid}/pdf", timeout=60)
if r.status_code == 200:
    with open("resume_v3.pdf", "wb") as f:
        f.write(r.content)
    print(f"PDF: resume_v3.pdf ({len(r.content):,} bytes)")
else:
    print(f"PDF download: {r.status_code} {r.text[:200]}")

import os
os.remove("_t.txt")
print("Done!")
