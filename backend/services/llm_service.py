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

def generate_question(file_text: str, answers: dict, questions_asked: list, analysis: dict = None) -> dict:
    str_answers = {k: v for k, v in answers.items() if isinstance(v, str)}
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in str_answers.items() if not q.startswith("_")]) if str_answers else "No answers yet."
    qa_text = "\n".join([f"- {q}" for q in questions_asked]) if questions_asked else "None"

    title_val = (analysis or {}).get("title", "")
    authors_val = (analysis or {}).get("authors") or []

    needs_title_confirm = title_val and title_val != "Unknown" and not answers.get("_title_ok") and not answers.get("_title_correct")
    needs_authors_confirm = not answers.get("_authors_ok")

    if needs_title_confirm:
        return {
            "ready": False,
            "question": f"The extracted paper title is: \"{title_val}\". Is this correct?",
            "options": ["Yes, correct", "No, let me type the correct title"],
            "context": "The title appears at the top of the paper.",
            "type": "title_confirm"
        }

    if not authors_val or all(a == "Author A" or a == "Author B" for a in authors_val):
        if not any("author" in q.lower() for q in questions_asked):
            return {
                "ready": False,
                "question": "Please provide the full name(s) of the author(s) for this paper. Separate multiple names with semicolons.",
                "options": ["John Smith", "John Smith; Jane Doe"],
                "context": "Author names are needed for the IEEE paper byline.",
                "type": "authors"
            }
    elif needs_authors_confirm:
        names_str = "; ".join(authors_val)
        return {
            "ready": False,
            "question": f"Are these authors correct: {names_str}?",
            "options": ["Yes, correct", "No, let me type the correct names"],
            "context": "Author names appear in the paper byline.",
            "type": "authors_confirm"
        }

    if not answers.get("_affiliation_ok") and authors_val:
        return {
            "ready": False,
            "question": "What is the institutional affiliation (university, lab, or hospital) for the authors?",
            "options": ["MIT", "Stanford University", "Indian Institute of Technology"],
            "context": "Affiliation appears below each author name in the IEEE format.",
            "type": "affiliation"
        }

    # Detect if user already said they have no more data
    user_said_no_more = any(
        isinstance(a, str) and a.strip().lower().startswith("no") and ("more" in q.lower() or "additional" in q.lower() or "detailed" in q.lower() or "details" in q.lower() or "full" in q.lower() or "complete" in q.lower())
        for q, a in answers.items()
    )

    prompt = f"""Based on the uploaded document and previous answers, check if enough info exists to write a complete IEEE research paper.

The user has already answered "No" to questions about having more/additional/full details.
{'The user has no further data to provide. Set ready=true and proceed with the available content.' if user_said_no_more else ''}

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
        {"role": "system", "content": "You help write a research paper. Keep questions simple, few, and in plain English. When the user says they have no more data, set ready=true and write the paper from what is available."},
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

    title = (analysis or {}).get("title", "Research Paper")
    domain = (analysis or {}).get("domain", "")
    keywords = (analysis or {}).get("keywords") or []
    present_sections = (analysis or {}).get("present_sections") or []
    authors_list = (analysis or {}).get("authors") or ["Author A", "Author B"]

    domain_instruction = f" The paper should focus on {domain}." if domain else ""
    kw_instruction = f" Key topics: {', '.join(keywords)}." if keywords else ""
    sections_instruction = f" The uploaded notes cover these sections: {', '.join(present_sections)}. Expand them into a full paper." if present_sections else ""

    prompt = f"""Write a complete IEEE-format research paper on the topic described below.

Title: {title}{domain_instruction}{kw_instruction}{sections_instruction}

Ground every claim in the document context below. You may invent plausible references (author, title, venue, year) for a realistic bibliography. Do NOT invent any numerical results, paper counts, statistics, or specific metrics not present in the document.

Structure the paper with these ##-prefixed sections in order:
- ## Abstract
- ## Introduction
- ## Literature Review
- ## Methodology
- ## Results and Discussion
- ## Conclusion
- ## References

Rules:
- Start with ## Abstract (one paragraph summarising the paper).
- Each ## section should be 2–4 paragraphs of focused analysis.
- Never include reasoning, chain-of-thought, thinking blocks, or meta-commentary. Output only the paper content.
- The ## References section must contain at least 5 IEEE-formatted references like: [1] J. Smith, "Title," Journal Name, vol. X, no. Y, pp. Z-Z, year.

Document context: {file_text[:12000]}

Author details: {answers_text}"""
    messages = [
        {"role": "system", "content": "You write IEEE-format research papers. You use only ##-prefixed section headings. You never include reasoning or chain-of-thought in your output."},
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
                "reasoning_effort": "none",
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
