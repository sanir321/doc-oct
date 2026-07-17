import requests, json, os, sys

BASE = "http://localhost:8000"

# 1. Health check
try:
    r = requests.get(f"{BASE}/", timeout=5)
    print(f"1. Health: {r.status_code} {r.json()}")
except Exception as e:
    print(f"1. Health: FAILED - {e}")
    sys.exit(1)

# 2. Upload a test file
try:
    with open("test_hello.txt", "w") as f:
        f.write("This is a test paper about machine learning classification using neural networks.")
    with open("test_hello.txt", "rb") as f:
        r = requests.post(f"{BASE}/api/upload", files={"file": ("test.txt", f, "text/plain")})
    print(f"2. Upload: {r.status_code}")
    data = r.json()
    sid = data.get("session_id", "")
    print(f"   session_id: {sid}")
except Exception as e:
    print(f"2. Upload: FAILED - {e}")
    sys.exit(1)

if not sid:
    print("No session_id returned. Check upload endpoint.")
    sys.exit(1)

# 3. Set mode (ieee)
try:
    r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "ieee"}, timeout=30)
    print(f"3. Set mode (ieee): {r.status_code}")
    data = r.json()
    print(f"   keys: {list(data.keys())}")
    print(f"   question: {str(data.get('question', ''))[:80] if data.get('question') else 'none'}")
    print(f"   analysis: {'present' if data.get('analysis') else 'none'}")
except Exception as e:
    print(f"3. Set mode: FAILED - {e}")
    data = {}

# 4. Submit answer
if data and data.get("question"):
    question = data["question"]
    try:
        r = requests.post(f"{BASE}/api/answer-paper/{sid}", json={
            "question": question,
            "answer": "This paper covers deep learning techniques for text classification using transformer architectures."
        }, timeout=30)
        print(f"4. Answer: {r.status_code}")
        resp = r.json()
        print(f"   ready: {resp.get('ready')}")
        print(f"   next_q: {str(resp.get('question', ''))[:80] if resp.get('question') else 'none'}")
        print(f"   follow_up: {str(resp.get('follow_up', ''))[:80] if resp.get('follow_up') else 'none'}")
    except Exception as e:
        print(f"4. Answer: FAILED - {e}")
else:
    print("4. Answer: SKIPPED - no question returned")

print()
print("--- Tests complete ---")
