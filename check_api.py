"""Check API response for author info."""
import httpx, json

B = "https://backend-production-a605.up.railway.app"

# Upload
with open("sample_test.txt", "rb") as f:
    r = httpx.post(f"{B}/api/upload", files={"file": ("sample_test.txt", f, "text/plain")}, timeout=30)
print(f"Upload: {r.status_code}")
data = r.json()
print(f"Analysis: {json.dumps(data.get('analysis', {}), indent=2)[:500]}")

# Check if analysis has authors
analysis = data.get("analysis", {})
print(f"\nauthors key exists: {'authors' in analysis}")
print(f"authors value: {analysis.get('authors')}")
print(f"title: {analysis.get('title')}")
print(f"domain: {analysis.get('domain')}")
print(f"keywords: {analysis.get('keywords')}")
