import requests, json, sys, os

BASE = "https://backend-production-a605.up.railway.app"

# 1. Upload a sample document with resume content
try:
    doc = """Professional Summary: Experienced software engineer with 5 years in full-stack development.
Skills: Python, JavaScript, React, Node.js, PostgreSQL, Docker, AWS.
Work Experience: Senior Developer at TechCorp (2021-2025). Built microservices and REST APIs.
Education: B.Tech in Computer Science, IIT Bombay (2016-2020).
Projects: Built an e-commerce platform with 10k+ daily users."""
    with open("_test_resume.txt", "w") as f:
        f.write(doc)
    with open("_test_resume.txt", "rb") as f:
        r = requests.post(f"{BASE}/api/upload", files={"file": ("resume.txt", f, "text/plain")}, timeout=15)
    print(f"1. Upload: {r.status_code}")
    data = r.json()
    sid = data.get("session_id", "")
    print(f"   session_id: {sid}")
except Exception as e:
    print(f"1. Upload: FAILED - {e}")
    sys.exit(1)

if not sid:
    print("No session ID")
    sys.exit(1)

# 2. Set mode to resume
try:
    r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "resume"}, timeout=60)
    print(f"2. Set resume mode: {r.status_code}")
    data = r.json()
    print(f"   ready: {data.get('ready')}")
    has_q = bool(data.get("question"))
    print(f"   has question: {has_q}")
    if has_q:
        print(f"   first q: {str(data['question'])[:120]}")
        print(f"   type: {data.get('type')}")
except Exception as e:
    print(f"2. Set resume mode: FAILED - {e}")
    sys.exit(1)

# 3. Answer questions until ready
max_q = 8
for i in range(max_q):
    if not data.get("question"):
        print(f"3.{i+1}. No more questions (ready={data.get('ready')})")
        break
    q = data["question"]
    qtype = data.get("type", "")
    if qtype in ("name_confirm", "email_confirm"):
        ans = "Yes, that's correct"
    elif qtype == "name":
        ans = "John Doe"
    elif qtype == "email":
        ans = "john@example.com"
    elif qtype == "phone":
        ans = "+1-555-1234"
    else:
        ans = "No more details" if i > 3 else "Yes, continue with what I have"
    try:
        r = requests.post(f"{BASE}/api/answer-resume/{sid}", json={"question": q, "answer": ans}, timeout=60)
        print(f"3.{i+1}. Answer [{qtype[:10]}]: {r.status_code}", end="")
        data = r.json()
        if data.get("ready"):
            print(f" ready=True")
            break
        print(f" next_q={bool(data.get('question'))}")
    except Exception as e:
        print(f" FAILED - {e}")
        break

# 4. Generate resume
try:
    r = requests.get(f"{BASE}/api/generate-resume-stream/{sid}", stream=True, timeout=180)
    print(f"4. Generate resume: {r.status_code}")
    if r.status_code == 200:
        tokens = 0
        done = False
        for line in r.iter_lines(decode_unicode=True):
            if not line or line.startswith(":"):
                continue
            if line.startswith("data: "):
                try:
                    ev = json.loads(line[6:])
                    if ev.get("type") == "token":
                        tokens += 1
                    elif ev.get("type") == "done":
                        result = ev.get("result", {})
                        rt = result.get("resume_text", "")
                        print(f"   DONE! tokens={tokens}, text_len={len(rt)}")
                        print(f"    Name: {result.get('resume_data', {}).get('name', '?')}")
                        print(f"    Email: {result.get('resume_data', {}).get('email', '?')}")
                        print(f"    Preview ({100} chars):")
                        for line2 in rt.split("\n")[:8]:
                            print(f"      {line2.strip()}")
                        done = True
                        break
                    elif ev.get("type") == "error":
                        print(f"   ERROR: {ev}")
                        done = True
                        break
                except:
                    pass
        if not done:
            print(f"   Stream ended without done")
except Exception as e:
    print(f"4. Generate: FAILED - {e}")

# 5. Download HTML
try:
    r = requests.get(f"{BASE}/api/download-resume/{sid}/html", timeout=30)
    print(f"5. Download HTML: {r.status_code} size={len(r.content):,}")
except Exception as e:
    print(f"5. Download: FAILED - {e}")

os.remove("_test_resume.txt")
print()
print("=== RESUME DEMO DONE ===")
