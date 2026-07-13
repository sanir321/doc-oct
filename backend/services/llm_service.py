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
    analysis = analysis or {}
    str_answers = {k: v for k, v in answers.items() if isinstance(k, str) and isinstance(v, str)}
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in str_answers.items() if not q.startswith("_")]) if str_answers else "No answers yet."
    qa_text = "\n".join([f"- {q}" for q in questions_asked]) if questions_asked else "None"

    title_val = analysis.get("title", "")
    authors_val = analysis.get("authors") or []
    keywords_val = analysis.get("keywords") or []
    has_abstract = analysis.get("has_abstract", False)
    present = analysis.get("present_sections") or []
    missing = analysis.get("missing_info") or []

    placeholder_authors = (not authors_val) or all(a in ("Author A", "Author B") for a in authors_val)

    # 1. TITLE — confirm if found, otherwise ask the user to supply it
    if title_val and title_val != "Unknown":
        if not answers.get("_title_ok") and not answers.get("_title_correct"):
            return {
                "ready": False,
                "question": f"I read your document and found the title: \"{title_val}\". Is that the title you want on the paper?",
                "options": ["Yes, that's correct", "No, I'll type a different title"],
                "context": "Confirming the paper title.",
                "type": "title_confirm"
            }
    elif not answers.get("_title_ok"):
        return {
            "ready": False,
            "question": "I couldn't find a clear title in your document. What should the paper be titled?",
            "options": ["Use the document's first line as the title", "I'll type the title"],
            "context": "A title is required for the paper.",
            "type": "title"
        }

    # 2. AUTHORS — only asked when the document has no usable author names
    if placeholder_authors:
        if not any("author" in q.lower() for q in questions_asked):
            return {
                "ready": False,
                "question": "Your document doesn't list any author names. Who should appear on the byline? (Separate multiple authors with semicolons.)",
                "options": ["John Smith", "John Smith; Jane Doe"],
                "context": "Author names are needed for the IEEE byline.",
                "type": "authors"
            }
    elif not answers.get("_authors_ok"):
        names_str = "; ".join(authors_val)
        return {
            "ready": False,
            "question": f"I extracted these author name(s): {names_str}. Are they correct?",
            "options": ["Yes, correct", "No, let me type the correct names"],
            "context": "Confirming author names.",
            "type": "authors_confirm"
        }

    # 3. AFFILIATION
    if authors_val and not answers.get("_affiliation_ok"):
        return {
            "ready": False,
            "question": "Thanks. What is the institutional affiliation (university, lab, or company) for the author(s)?",
            "options": ["MIT", "Stanford University", "Indian Institute of Technology"],
            "context": "Affiliation appears below each author name.",
            "type": "affiliation"
        }

    # 4. EMAIL (never present in a document, so always collect it)
    if authors_val and not answers.get("_email_ok"):
        return {
            "ready": False,
            "question": "And a contact email for the corresponding author, so readers can reach you?",
            "options": ["author@example.com"],
            "context": "Email appears in the IEEE author block.",
            "type": "email"
        }

    # 5. KEYWORDS — only if the document didn't supply any
    if not keywords_val and not answers.get("_keywords_ok"):
        return {
            "ready": False,
            "question": "Lastly, what keywords should I index this paper under? (Comma-separated, e.g. reinforcement learning, drones, navigation)",
            "options": ["machine learning, robotics", "deep learning, control systems"],
            "context": "Index Terms help readers find the paper.",
            "type": "keywords"
        }

    # 6. CONTENT GAPS — let the LLM ask about genuinely missing paper content
    user_said_no_more = any(
        isinstance(a, str) and a.strip().lower().startswith("no") and any(w in q.lower() for w in ("more", "additional", "detailed", "details", "full", "complete"))
        for q, a in answers.items()
    )
    found = []
    if title_val:
        found.append("a title")
    if has_abstract:
        found.append("an abstract")
    if present:
        found.append("these sections: " + ", ".join(present))
    found_str = ", ".join(found) if found else "very little structured content"
    miss_str = "; ".join(missing) if missing else "some details"

    prompt = f"""You are helping turn an uploaded document into an IEEE research paper. The bibliographic details (title, authors, affiliation, email, keywords) have already been collected from the user.

What was found in the document: {found_str}.
What appears to be missing or thin: {miss_str}.

Previous answers from the user:
{answers_text}

Questions already asked: {qa_text}

Your job: decide if you have enough to write a complete, accurate IEEE paper, or ask the user to fill ONE specific content gap.

{'The user has indicated they have no more data. Set ready=true and write the paper from what is available.' if user_said_no_more else ''}

Rules:
- If enough info exists, respond: {{"ready": true}}
- Otherwise ask AT MOST 1 question, in plain, friendly, conversational English.
- Reference what you already know; ask only about a genuinely missing detail (e.g. methodology, results, datasets, contributions).
- Do NOT re-ask for title, authors, affiliation, email, or keywords — those are already collected.
- Be generous about being ready; only ask if a key part of the paper cannot be written at all.

If asking: {{"ready": false, "question": "...", "options": ["short example 1", "short example 2"], "context": "why needed"}}"""
    return call_llm_json([
        {"role": "system", "content": "You help write IEEE papers. Ask the user only about genuinely missing content, in friendly plain English. When the user has no more data, return ready=true."},
        {"role": "user", "content": f"Document: {file_text[:5000]}\n\n{prompt}"}
    ])

def edit_paper(paper_text: str, instruction: str, current_title: str = "") -> str:
    prompt = f"""You are editing an IEEE-format research paper based on the user's instruction.

CURRENT TITLE: {current_title or "(unknown)"}

CURRENT PAPER:
{paper_text}

INSTRUCTION: {instruction}

Rewrite the COMPLETE paper applying the instruction. Strictly preserve the existing ##-prefixed section structure of the CURRENT PAPER — only include the sections that are already present, in their current order. Do NOT invent or add new sections (such as Literature Review, Methodology, Results, Limitations, or About the Authors) unless the instruction explicitly asks for them. Preserve all unchanged content verbatim. Do NOT invent numerical results, statistics, or metrics not already present.
If the instruction changes the paper title, output the new title as the VERY FIRST LINE in the exact format: # New Title
Otherwise, do not include any top-level title line.
Never include reasoning, chain-of-thought, or commentary — output only the revised paper."""
    messages = [
        {"role": "system", "content": "You edit IEEE-format research papers using only ##-prefixed section headings. Output only the paper, never reasoning or commentary. Never add sections that aren't in the current paper."},
        {"role": "user", "content": prompt}
    ]
    text = call_llm(messages, temperature=0.4, max_tokens=16384)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return text.strip()

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

Ground every claim in the document context below. You may invent plausible references (author, title, venue, year) and a brief professional bio for each author for a realistic bibliography and About the Authors section. Do NOT invent any numerical results, paper counts, statistics, or specific metrics not present in the document.

Structure the paper with these ##-prefixed sections in order:
- ## Abstract
- ## Introduction
- ## Literature Review
- ## Methodology
- ## Results and Discussion
- ## Conclusion
- ## References
- ## About the Authors

Rules:
- Start with ## Abstract (one paragraph summarising the paper).
- Each ## section should be 2–4 paragraphs of focused analysis.
- The ## References section must contain at least 5 IEEE-formatted references like: [1] J. Smith, "Title," Journal Name, vol. X, no. Y, pp. Z-Z, year.
- The ## About the Authors section must list each author (bold name) with a 1–2 sentence professional biography.
- If helpful, you may include one markdown table (using | separators) inside a body section, with a "Table 1. ..." caption line above it.
- Never include reasoning, chain-of-thought, thinking blocks, or meta-commentary. Output only the paper content.

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


def analyze_document_for_resume(file_text: str) -> dict:
    """Extract resume-relevant info from a document."""
    prompt = f"""Read this document and extract resume/CV information as JSON:
{{
  "name": "full name or empty string",
  "email": "email or empty string",
  "phone": "phone or empty string",
  "education": ["Degree — School, Year"],
  "experience": ["Role — Company, Dates — brief description"],
  "skills": ["skill1", "skill2"],
  "summary": "brief professional summary or empty string",
  "projects": ["Project name — brief description"],
  "certifications": ["cert1"]
}}

If a field is not found, use an empty string or empty array. Do not invent information.

Document content:
{file_text[:15000]}"""
    return call_llm_json([
        {"role": "system", "content": "You extract resume metadata from documents. Return only valid JSON."},
        {"role": "user", "content": prompt}
    ])


def generate_resume_question(file_text: str, answers: dict, questions_asked: list, analysis: dict = None) -> dict:
    """Generate the next resume-specific interview question."""
    analysis = analysis or {}
    str_answers = {k: v for k, v in answers.items() if isinstance(k, str) and isinstance(v, str)}
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in str_answers.items() if not q.startswith("_")]) if str_answers else "No answers yet."
    qa_text = "\n".join([f"- {q}" for q in questions_asked]) if questions_asked else "None"

    # Check what we already have from the document or user
    has_name = bool(analysis.get("name"))
    has_email = bool(analysis.get("email"))
    has_phone = bool(analysis.get("phone"))
    has_education = bool(analysis.get("education"))
    has_experience = bool(analysis.get("experience"))
    has_skills = bool(analysis.get("skills"))
    has_summary = bool(analysis.get("summary"))

    # Structured gates first (like IEEE does for title/authors)
    if has_name and not answers.get("_name_ok"):
        return {
            "ready": False,
            "question": f"I found the name \"{analysis['name']}\" in your document. Is that correct?",
            "options": ["Yes, that's correct", "No, I'll type my name"],
            "context": "Confirming your full name.",
            "type": "name_confirm"
        }

    if not has_name and not answers.get("_name_ok"):
        return {
            "ready": False,
            "question": "What is your full name?",
            "options": ["John Smith"],
            "context": "Your name for the resume header.",
            "type": "name"
        }

    if has_email and not answers.get("_email_ok"):
        return {
            "ready": False,
            "question": f"I found the email \"{analysis['email']}\". Is that your contact email?",
            "options": ["Yes, that's correct", "No, I'll type a different email"],
            "context": "Contact email for the resume.",
            "type": "email_confirm"
        }

    if not has_email and not answers.get("_email_ok"):
        return {
            "ready": False,
            "question": "What is your email address for the resume?",
            "options": ["john@example.com"],
            "context": "Contact email.",
            "type": "email"
        }

    if not has_phone and not answers.get("_phone_ok"):
        return {
            "ready": False,
            "question": "What is your phone number?",
            "options": ["+1 (555) 123-4567"],
            "context": "Phone number for the resume header.",
            "type": "phone"
        }

    # Let the LLM handle the rest (education, experience, skills, summary gaps)
    user_said_no_more = any(
        isinstance(a, str) and a.strip().lower().startswith("no") and any(w in q.lower() for w in ("more", "additional", "details"))
        for q, a in answers.items()
    )

    found = []
    if has_education: found.append("education")
    if has_experience: found.append("work experience")
    if has_skills: found.append("skills")
    if has_summary: found.append("a professional summary")
    found_str = ", ".join(found) if found else "very little structured content"

    prompt = f"""You are helping build a professional resume from an uploaded document.

What was found in the document: {found_str}.
Name: {analysis.get('name', 'not provided')}.
Email: {analysis.get('email', 'not provided')}.
Phone: {analysis.get('phone', 'not provided')}.
Education: {analysis.get('education', [])}
Experience: {analysis.get('experience', [])}
Skills: {analysis.get('skills', [])}

Previous answers from the user:
{answers_text}

Questions already asked: {qa_text}

Your job: decide if you have enough to write a complete resume, or ask the user to fill ONE specific gap.

{'The user has indicated they have no more data. Set ready=true and write the resume from what is available.' if user_said_no_more else ''}

Rules:
- If enough info exists, respond: {{"ready": true}}
- Otherwise ask AT MOST 1 question about missing resume content (education, experience, skills, etc.)
- Do NOT re-ask for name, email, or phone — those are already collected.
- Be generous about being ready; only ask if a key resume section would be empty.

If asking: {{"ready": false, "question": "...", "options": ["short example 1", "short example 2"], "context": "why needed"}}"""
    return call_llm_json([
        {"role": "system", "content": "You help build resumes. Ask about missing content (education, experience, skills). When enough info exists, return ready=true."},
        {"role": "user", "content": f"Document: {file_text[:5000]}\n\n{prompt}"}
    ])


def generate_resume_stream(file_text: str, answers: dict, analysis: dict):
    """Stream a complete resume as markdown, section by section."""
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items() if not q.startswith("_")]) if answers else ""

    name = analysis.get("name", "Your Name")
    email = analysis.get("email", "")
    phone = analysis.get("phone", "")
    education = analysis.get("education", [])
    experience = analysis.get("experience", [])
    skills = analysis.get("skills", [])
    summary = analysis.get("summary", "")

    prompt = f"""Write a professional resume in clean markdown format.

Contact Info:
- Name: {name}
- Email: {email}
- Phone: {phone}

Use these ##-prefixed sections in order:
- ## Summary
- ## Education
- ## Experience
- ## Skills
- ## Projects
- ## Certifications

Rules:
- Start with ## Summary (2-3 sentence professional summary based on the document).
- For ## Education, list each entry as: **Degree** — School, Year with GPA if available.
- For ## Experience, use ### sub-headings: ### Role — Company, Dates then bullet points for achievements.
- For ## Skills, group by category (Languages, Frameworks, Tools, etc.) as bullet points.
- For ## Projects, use bold names with brief descriptions.
- For ## Certifications, simple bullet list.
- Only include sections that have content. Skip empty sections.
- Never invent specific numbers, metrics, or achievements not mentioned in the source document.
- Never include reasoning or commentary — output only the resume content.

Document context: {file_text[:12000]}

Additional details from user: {answers_text}"""
    messages = [
        {"role": "system", "content": "You write professional resumes in clean markdown. Use only ##-prefixed section headings. Output only the resume, never commentary."},
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
                    token = delta.get("content", "") or delta.get("reasoning", "")
                    if token:
                        yield token
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue


def edit_resume(resume_text: str, instruction: str) -> str:
    """Edit a resume based on user instruction."""
    prompt = f"""You are editing a professional resume based on the user's instruction.

CURRENT RESUME:
{resume_text}

INSTRUCTION: {instruction}

Rewrite the COMPLETE resume applying the instruction. Strictly preserve the existing ##-prefixed section structure — only include sections that are already present, in their current order. Do NOT invent or add new sections unless the instruction explicitly asks for them. Preserve all unchanged content verbatim. Do NOT invent specific numbers, metrics, or achievements not already present.
Never include reasoning, chain-of-thought, or commentary — output only the revised resume."""
    messages = [
        {"role": "system", "content": "You edit professional resumes using only ##-prefixed section headings. Output only the resume, never reasoning or commentary."},
        {"role": "user", "content": prompt}
    ]
    text = call_llm(messages, temperature=0.4, max_tokens=16384)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return text.strip()
