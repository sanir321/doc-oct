import httpx
import json
from config import OPENCODE_ZEN_API_KEY, OPENCODE_ZEN_BASE_URL, LLM_MODEL

def call_llm(messages, temperature=0.7, max_tokens=8192):
    resp = httpx.post(
        f"{OPENCODE_ZEN_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {OPENCODE_ZEN_API_KEY}"},
        json={
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=300
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def call_llm_json(messages, temperature=0.3, max_tokens=4096):
    text = call_llm(messages, temperature, max_tokens).strip()
    if text.startswith("```"): text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return json.loads(text.strip())

def analyze_document(file_text: str) -> dict:
    prompt = f"""Read this document and extract IEEE paper information as JSON:
{{
  "title": "...",
  "present_sections": ["Abstract", "Introduction", ...],
  "missing_info": ["specific details still needed"],
  "authors": ["name1", "name2"],
  "keywords": ["keyword1", ...],
  "has_abstract": true/false,
  "domain": "research domain"
}}

Document content:
{file_text[:15000]}"""
    return call_llm_json([
        {"role": "system", "content": "You extract IEEE paper metadata from documents. Return only valid JSON."},
        {"role": "user", "content": prompt}
    ])

def generate_question(file_text: str, answers: dict, questions_asked: list) -> dict:
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()]) if answers else "No answers yet."
    qa_text = "\n".join([f"- {q}" for q in questions_asked]) if questions_asked else "None"
    prompt = f"""Based on the uploaded document and previous answers, check if enough info exists to write a complete IEEE research paper.

Questions already asked: {qa_text}

Previous answers:
{answers_text}

Rules:
- If enough info exists, respond with: {{"ready": true}}
- If you MUST ask, ask AT MOST 1 question per response.
- Use plain, simple language — avoid technical jargon.
- Prioritize being "ready" — only ask if truly necessary.
- Never ask more than 3 questions total across all rounds.

If asking: {{
  "ready": false,
  "question": "A simple question in plain English",
  "options": ["Simple option 1", "Simple option 2"],
  "context": "Briefly why this is needed"
}}
"""
    return call_llm_json([
        {"role": "system", "content": "You help write a research paper. Keep questions simple, few, and in plain English."},
        {"role": "user", "content": f"Document: {file_text[:5000]}\n\n{prompt}"}
    ])

def check_answer_clear(file_text: str, question: str, answer: str) -> dict:
    prompt = f"""The user answered: "{answer}" to the question: "{question}"

Be generous — accept the answer as clear unless it's truly empty or off-topic.
If clear: {{"clear": true}}
If unclear (rare): {{"clear": false, "follow_up": "A simple clarifying question in plain English", "options": ["Simple option 1", "Simple option 2"]}}
"""
    return call_llm_json([
        {"role": "system", "content": "Be generous — accept answers as clear unless they're empty or completely off-topic."},
        {"role": "user", "content": prompt}
    ])

def generate_paper_stream(file_text: str, answers: dict, analysis: dict):
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()]) if answers else ""
    prompt = f"""Write a complete IEEE conference research paper based on this information.

Uploaded document context:
{file_text[:12000]}

Additional details from author:
{answers_text}

Write the full paper content with ## section headings. Include: Abstract, Introduction, Literature Review, Methodology, Implementation, Results & Discussion, Conclusion, References.

IMPORTANT: Use ONLY the facts from the uploaded document and author answers."""
    messages = [
        {"role": "system", "content": "You are an IEEE research paper generator. Write the paper directly with ## section headings."},
        {"role": "user", "content": prompt}
    ]
    with httpx.Client(timeout=300) as client:
        with client.stream(
            "POST",
            f"{OPENCODE_ZEN_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENCODE_ZEN_API_KEY}"},
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 16384,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    choices = chunk.get("choices")
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    reasoning = delta.get("reasoning", "")
                    token = content or reasoning or ""
                    if token:
                        yield token
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue
