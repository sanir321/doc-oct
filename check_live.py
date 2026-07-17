import requests, json, sys

BASE = "https://backend-production-a605.up.railway.app"

# 1. Health
try:
    r = requests.get(f"{BASE}/", timeout=10)
    print(f"1. Health: {r.status_code} {r.json()}")
except Exception as e:
    print(f"1. Health: FAILED - {e}")
    sys.exit(1)

# 2. Upload
try:
    with open("test_hello.txt", "w") as f:
        f.write("Deep learning for medical image classification using convolutional neural networks and transfer learning.")
    with open("test_hello.txt", "rb") as f:
        r = requests.post(f"{BASE}/api/upload", files={"file": ("paper.txt", f, "text/plain")}, timeout=15)
    print(f"2. Upload: {r.status_code}")
    data = r.json()
    sid = data.get("session_id", "")
    print(f"   session_id: {sid}")
    print(f"   response: {json.dumps(data)[:200]}")
except Exception as e:
    print(f"2. Upload: FAILED - {e}")
    sys.exit(1)

if sid:
    # 3. Set mode (ieee)
    try:
        r = requests.post(f"{BASE}/api/set-mode/{sid}", json={"mode": "ieee"}, timeout=60)
        print(f"3. Set mode: {r.status_code}")
        data = r.json()
        print(f"   has analysis: {bool(data.get('analysis'))}")
        print(f"   has question: {bool(data.get('question'))}")
        q1 = data.get("question", "")
        print(f"   first q: {str(q1)[:100]}")
    except Exception as e:
        print(f"3. Set mode: FAILED - {e}")
        data = {}
    
    # 4. Answer first question
    if data.get("question"):
        try:
            r = requests.post(f"{BASE}/api/answer-paper/{sid}", json={
                "question": data["question"],
                "answer": "The paper focuses on using deep CNNs for classifying medical images like X-rays and MRIs. Key methods include ResNet and EfficientNet architectures."
            }, timeout=60)
            print(f"4. Answer 1: {r.status_code}")
            resp = r.json()
            print(f"   ready: {resp.get('ready')}")
            has_followup = bool(resp.get("follow_up"))
            has_next_q = bool(resp.get("question"))
            print(f"   follow_up: {has_followup}, next_q: {has_next_q}")
            if resp.get("question"):
                print(f"   q2: {str(resp['question'])[:100]}")
        except Exception as e:
            print(f"4. Answer 1: FAILED - {e}")
    
    # 5. Generate paper
    try:
        r = requests.get(f"{BASE}/api/generate-paper-stream/{sid}", stream=True, timeout=180)
        print(f"5. Generate stream: {r.status_code}")
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
                            print(f"   DONE! tokens={tokens}, has_result={bool(ev.get('result'))}")
                            done = True
                            break
                        elif ev.get("type") == "error":
                            print(f"   ERROR: {ev}")
                            done = True
                            break
                    except:
                        pass
            if not done:
                print(f"   Stream ended without done/error. tokens={tokens}")
            else:
                print(f"   Total tokens: {tokens}")
        else:
            print(f"   body: {r.text[:200]}")
    except Exception as e:
        print(f"5. Generate: FAILED - {e}")

    # 6. Download
    try:
        r = requests.get(f"{BASE}/api/download-paper/{sid}/pdf?format=iemt", timeout=60)
        print(f"6. Download PDF (IEMT): {r.status_code} size={len(r.content):,}")
        r = requests.get(f"{BASE}/api/download-paper/{sid}/html", timeout=30)
        print(f"7. Download HTML: {r.status_code} size={len(r.content):,}")
    except Exception as e:
        print(f"6/7. Download: FAILED - {e}")

print()
print("=== TESTS DONE ===")
