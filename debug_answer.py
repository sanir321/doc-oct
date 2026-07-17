import requests, json

BASE = "https://backend-production-a605.up.railway.app"

# Upload a small file
with open("test_hello.txt", "w") as f:
    f.write("Deep learning for medical image classification using CNNs.")
with open("test_hello.txt", "rb") as f:
    r = requests.post(f"{BASE}/api/upload", files={"file": ("paper.txt", f, "text/plain")})
sid = r.json()["session_id"]
print(f"Session: {sid}")

# Set mode
r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "ieee"}, timeout=60)
q = r.json()
print(f"Set-mode: {q.keys()}")
question_str = q.get("question", "")
if isinstance(question_str, dict):
    question_str = question_str.get("question", question_str.get("text", ""))
print(f"Question: {question_str[:100]}")

# Try to answer - get full error details
r = requests.post(f"{BASE}/api/answer-paper/{sid}", json={
    "question": question_str,
    "answer": "Test answer about deep learning."
}, timeout=60)
print(f"Answer status: {r.status_code}")
print(f"Answer body: {r.text[:500]}")
