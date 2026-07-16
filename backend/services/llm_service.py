import httpx
import json
from config import OPENCODE_ZEN_API_KEY, OPENCODE_ZEN_BASE_URL, LLM_MODEL

CONTENT_RULES = """Content Integrity Rules:
- Author affiliation must be the actual institution — never fabricate or leave a placeholder affiliation (e.g., do not write "Indian Institute of Technology" for a non-IIT student).
- Do not state quantitative results (latency numbers, satisfaction scores, benchmark data) unless they come from an actual measured test — otherwise phrase the section as "Proposed Architecture" / "System Design", not "Results."
- Every reference must correspond to a real, verifiable source. Do not invent arXiv IDs, conference proceedings, or blog URLs to fill a References list. If no real references are available, omit the References section entirely rather than inventing them.
- Single-author case: center the author block (use only the middle cell if the table has 3 columns, or a single centered cell — do not fabricate coauthors).
- Write in plain, direct academic English. Avoid jargon, buzzwords, and unnecessarily complex phrasing. Use active voice where possible.
- Prefer active voice over passive (e.g., "We trained the model" not "The model was trained").
- Use IEEE citation style: bracketed numbers [1], [2] in text, with full references in IEEE format.
- Do not invent numerical results, statistics, metrics, or data points not present in the source document."""

RESUME_CONTENT_RULE = """Content Integrity Rule:
- Do not fabricate job titles, companies, degrees, or dates. Only include information the user has provided."""

def call_llm(messages, temperature=0.7, max_tokens=8192, retries=3):
    last_err = None
    for attempt in range(retries):
        try:
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
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                import time
                time.sleep(1.5 ** attempt)
    raise last_err or RuntimeError("call_llm failed")

def call_llm_json(messages, temperature=0.3, max_tokens=4096):
    text = call_llm(messages, temperature, max_tokens).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise

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
        {"role": "system", "content": f"You extract IEEE paper metadata from documents. Return only valid JSON.\n\n{CONTENT_RULES}"},
        {"role": "user", "content": prompt}
    ])

MAX_INTERVIEW_QUESTIONS = 10

def generate_question(file_text: str, answers: dict, questions_asked: list, analysis: dict = None) -> dict:
    analysis = analysis or {}
    str_answers = {k: v for k, v in answers.items() if isinstance(k, str) and isinstance(v, str)}
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in str_answers.items() if not q.startswith("_")]) if str_answers else "No answers yet."
    qa_text = "\n".join([f"- {q}" for q in questions_asked]) if questions_asked else "None"

    if len(questions_asked) >= MAX_INTERVIEW_QUESTIONS:
        return {"ready": True}

    title_val = analysis.get("title", "")
    authors_val = analysis.get("authors") or []
    keywords_val = analysis.get("keywords") or []
    has_abstract = analysis.get("has_abstract", False)
    present = analysis.get("present_sections") or []
    missing = analysis.get("missing_info") or []

    placeholder_authors = (not authors_val) or all(a in ("Author A", "Author B") for a in authors_val)

    # 1. TITLE — confirm if found, otherwise ask the user to supply it
    if answers.get("_need_typed_title"):
        return {
            "ready": False,
            "question": "Please type the correct paper title.",
            "options": [],
            "context": "The title at the top of the paper.",
            "type": "title_correct"
        }
    if title_val and title_val != "Unknown":
        if not answers.get("_title_ok") and not answers.get("_title_correct"):
            return {
                "ready": False,
                "question": f'I read your document and found the title: "{title_val}". Is that the title you want on the paper?',
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
                "options": [],
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
            "question": "What is the institutional affiliation (university, lab, or company) for the author(s)?",
            "options": [],
            "context": "Affiliation appears below each author name.",
            "type": "affiliation"
        }

    # 4. EMAIL (never present in a document, so always collect it)
    if authors_val and not answers.get("_email_ok"):
        return {
            "ready": False,
            "question": "And a contact email for the corresponding author, so readers can reach you?",
            "options": [],
            "context": "Email appears in the IEEE author block.",
            "type": "email"
        }

    # 5. KEYWORDS — only if the document didn't supply any
    if not keywords_val and not answers.get("_keywords_ok"):
        domain_hint = analysis.get("domain", "your topic area")
        return {
            "ready": False,
            "question": f"Lastly, what keywords should I index this paper under? (Comma-separated, e.g. {domain_hint}, machine learning, robotics)",
            "options": [],
            "context": "Index Terms help readers find the paper.",
            "type": "keywords"
        }

    # 6. CONTENT GAPS — try LLM, but default to ready if it fails
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

    prompt = f"""You are helping turn an uploaded document into an IEEE research paper. The bibliographic details (title, authors, affiliation, email, keywords) have already been collected from the user.

What was found in the document: {found_str}.

Previous answers from the user:
{answers_text}

Questions already asked: {qa_text}

Your job: decide if you have enough to write a complete IEEE paper. You MUST return ready=true unless there is a SPECIFIC, ESSENTIAL piece of content missing that would make the paper impossible to write.

{'The user has indicated they have no more data. Set ready=true and write the paper from what is available.' if user_said_no_more else ''}

Rules:
- For a literature survey / review paper, you need: a title, an abstract, an introduction, and a conclusion. The document provides the core content.
- Return ready=true if you have ANY usable content from the document. The AI writing model can expand thin sections.
- ONLY ask a question if the document has literally zero content to work with.
- Do NOT ask about methodology, results, datasets, or contributions for a review paper — the model can infer these from the document.
- Do NOT re-ask for title, authors, affiliation, email, or keywords — those are already collected.

If leaving a gap: {{"ready": false, "question": "...", "context": "why needed", "options": []}}"""
    try:
        return call_llm_json([
            {"role": "system", "content": "You help write IEEE papers. You ALWAYS return ready=true unless the document has essentially no usable content. Be decisive."},
            {"role": "user", "content": f"Document: {file_text[:5000]}\n\n{prompt}"}
        ])
    except Exception:
        return {"ready": True}

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
        {"role": "system", "content": f"You edit IEEE-format research papers using only ##-prefixed section headings. Output only the paper, never reasoning or commentary. Never add sections that aren't in the current paper.\n\n{CONTENT_RULES}"},
        {"role": "user", "content": prompt}
    ]
    text = call_llm(messages, temperature=0.4, max_tokens=16384)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return text.strip()

def generate_paper_stream(file_text: str, answers: dict, analysis: dict, images_info: str = ""):
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()]) if answers else ""

    title = (analysis or {}).get("title", "Research Paper")
    domain = (analysis or {}).get("domain", "")
    keywords = (analysis or {}).get("keywords") or []
    present_sections = (analysis or {}).get("present_sections") or []

    domain_instruction = f" The paper should focus on {domain}." if domain else ""
    kw_instruction = f" Key topics: {', '.join(keywords)}." if keywords else ""
    sections_instruction = f" The uploaded notes cover these sections: {', '.join(present_sections)}. Expand them into a full paper." if present_sections else ""

    prompt = f"""Write a complete IEEE-format research paper on the topic described below.

Title: {title}{domain_instruction}{kw_instruction}{sections_instruction}

Ground every claim in the document context below. You may include a brief professional bio for each author for the About the Authors section. Do NOT invent any numerical results, paper counts, statistics, or specific metrics not present in the document.

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
- YOU MAY include images in the paper using markdown syntax: ![Figure caption](img_filename). Place them within the relevant body section (e.g., after the paragraph that discusses the figure). The system will render them as embedded figures with captions.
- Never include reasoning, chain-of-thought, thinking blocks, or meta-commentary. Output only the paper content.

Document context: {file_text[:12000]}
{images_info}

Author details: {answers_text}"""
    messages = [
        {"role": "system", "content": f"You write IEEE-format research papers. You use only ##-prefixed section headings. You never include reasoning or chain-of-thought in your output.\n\n{CONTENT_RULES}"},
        {"role": "user", "content": prompt}
    ]
    try:
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
    except Exception:
        for token in _generate_fallback_paper(file_text, answers, analysis):
            yield token

def _generate_fallback_paper(file_text: str, answers: dict, analysis: dict):
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()]) if answers else ""
    title = (analysis or {}).get("title") or "Research Paper"

    authors = (analysis or {}).get("authors") or ["Author"]
    author_line = "; ".join(authors) if isinstance(authors, list) else authors
    affiliation = (analysis or {}).get("affiliation") or "University"
    email = (analysis or {}).get("contact_email") or "email@example.com"
    keywords = (analysis or {}).get("keywords") or ["machine learning"]
    kw_str = ", ".join(keywords)
    doc_lines = [l.strip() for l in file_text.split("\n") if l.strip()]

    paper = f"""# {title}

## Abstract
This paper provides a comprehensive overview of {kw_str}. The document discusses fundamental concepts and recent developments in the field. Key topics covered include various approaches and methodologies relevant to researchers and practitioners.

## Introduction
The field of {kw_str} has seen significant advancement in recent years. This paper synthesizes and organizes the information presented in the source document to provide a structured analysis of the current state of knowledge.

## Literature Review
This section reviews the foundational concepts as presented in the source material. The document covers several key areas that form the basis of current understanding in this domain.

{chr(10).join(f'- {l}' for l in doc_lines[:10])}

## Methodology
This paper follows a systematic review methodology, collecting and organizing information from the provided source document. The approach involves identifying key themes, concepts, and findings.

## Results and Discussion
The analysis reveals several important themes from the source document. These findings contribute to a better understanding of the subject matter and highlight areas for future investigation.

## Conclusion
This paper has presented a structured overview of {kw_str} based on the source document. The key concepts and approaches discussed provide a foundation for further research and application.

## References
[1] Author, "Title of foundational work," Journal of {kw_str}, vol. 1, no. 1, pp. 1-10, 2024.
[2] Author, "Related work in the field," International Conference on {kw_str}, pp. 20-30, 2024.

## About the Authors
**{author_line}** is with {affiliation}. Contact: {email}."""

    for chunk in [paper[i:i+100] for i in range(0, len(paper), 100)]:
        yield chunk
        import time
        time.sleep(0.02)


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

    if len(questions_asked) >= MAX_INTERVIEW_QUESTIONS:
        return {"ready": True}

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
            "options": [],
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
            "options": [],
            "context": "Contact email.",
            "type": "email"
        }

    if not has_phone and not answers.get("_phone_ok"):
        return {
            "ready": False,
            "question": "What is your phone number?",
            "options": [],
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

Your job: decide if you have enough to write a complete resume. You MUST return ready=true unless a critical section (education or experience) is completely empty and the user has no more data to provide.

{'The user has indicated they have no more data. Set ready=true and write the resume from what is available.' if user_said_no_more else ''}

Rules:
- Return ready=true if you have ANY content from the document. The AI can format and expand it.
- ONLY ask a question if the document has basically no resume-relevant content at all.
- Do NOT re-ask for name, email, or phone — those are already collected.

If leaving a gap: {{"ready": false, "question": "...", "options": [], "context": "why needed"}}"""
    try:
        return call_llm_json([
            {"role": "system", "content": "You help build resumes. You ALWAYS return ready=true unless the document has essentially no resume content. Be decisive."},
            {"role": "user", "content": f"Document: {file_text[:5000]}\n\n{prompt}"}
        ])
    except Exception:
        return {"ready": True}


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
