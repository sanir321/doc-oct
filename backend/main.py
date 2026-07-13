from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
import uvicorn
import os, re, uuid, tempfile, json
import PyPDF2
from docx import Document
from config import MAX_FILE_SIZE, UPLOAD_DIR
from services.llm_service import (
    analyze_document, generate_question, generate_paper_stream, edit_paper,
    analyze_document_for_resume, generate_resume_question, generate_resume_stream, edit_resume
)

app = FastAPI(title="Research Paper Generator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

sessions = {}

def _render_body(content):
    """Turn raw section text into HTML: paragraphs, markdown tables, captions."""
    def esc(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def is_sep(line):
        s = line.strip().strip("|")
        return bool(s) and set(s) <= set("-: |") and "-" in s
    def is_caption(s):
        return bool(re.match(r'^(figure|table)\s*\d*\.?\s', s, re.I))
    def md_table(rows):
        def cells(r):
            return [c.strip() for c in r.strip().strip("|").split("|")]
        header = cells(rows[0])
        body = [cells(r) for r in rows[2:] if "|" in r]
        th = "".join(f'<th class="tablehead">{esc(c)}</th>' for c in header)
        trs = "".join(
            "<tr>" + "".join(f'<td class="tabletext">{esc(c)}</td>' for c in r) + "</tr>"
            for r in body
        )
        return f'<table class="ieee-table"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'

    lines = [l.rstrip() for l in content.split("\n")]
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if "|" in stripped and i + 1 < n and is_sep(lines[i + 1]):
            rows = []
            while i < n and "|" in lines[i].strip():
                rows.append(lines[i].strip())
                i += 1
            out.append(md_table(rows))
            continue
        if is_caption(stripped):
            out.append(f'<div class="caption">{esc(stripped)}</div>')
            i += 1
            continue
        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and "|" not in lines[i] and not is_sep(lines[i]) and not is_caption(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f'<p>{esc(" ".join(para))}</p>')
    return "".join(out)

def generate_ieee_html(title, authors, abstract, sections, keywords, domain, references=None):
    # Build author HTML with per-affiliation superscript markers
    authors_html = ""
    if authors:
        affil_map = {}
        counter = 1
        author_parts = []
        for a in authors:
            affil = a.get("affiliation", "")
            if affil:
                if affil not in affil_map:
                    affil_map[affil] = counter
                    counter += 1
                sup = f'<sup>{affil_map[affil]}</sup>'
            else:
                sup = ""
            email = a.get("email", "")
            email_html = f'<br><span class="email">{email}</span>' if email else ""
            author_parts.append(
                f'<div class="author">{a["name"]}{sup}<br><span class="affil">{affil}</span>{email_html}</div>'
            )
        authors_html = "".join(author_parts)

    sections_html = "".join(
        f'<div class="section"><h2>{s["title"]}</h2>{_render_body(s["content"])}</div>'
        for s in sections
    )
    keywords_str = ", ".join(keywords)

    # Build references HTML
    refs_html = ""
    if references:
        ref_list = "\n".join(
            f'<p>[{i}] {r["citation"]}</p>' for i, r in enumerate(references, 1)
        )
        refs_html = f'<div class="references"><h2>References</h2>\n{ref_list}\n</div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{title}</title>
<style>
  @page {{ size: letter; margin: 0.75in 0.65in; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Times New Roman", Times, serif; font-size: 10pt; line-height: 1.15; color: #000; background: #fff; }}
  .paper {{ max-width: 7.5in; margin: 0 auto; }}
  h1 {{ font-size: 24pt; text-align: center; font-weight: bold; margin-bottom: 16px; font-family: "Times New Roman", Times, serif; letter-spacing: normal; }}
  .authors {{ text-align: center; font-size: 12pt; margin-bottom: 18px; font-family: "Times New Roman", Times, serif; }}
  .author {{ display: inline-block; margin: 0 16px; }}
  .affil {{ font-size: 10pt; font-style: italic; }}
  .email {{ font-size: 10pt; }}
  sup {{ font-size: 8pt; vertical-align: super; line-height: 1; }}
  .abstract {{ margin: 12px 0; padding: 0; }}
  .abstract-label {{ font-size: 10pt; font-weight: bold; font-style: italic; }}
  .abstract p {{ font-size: 10pt; font-weight: bold; font-style: italic; text-align: justify; display: inline; }}
  .kw-label {{ font-size: 10pt; font-weight: bold; font-style: italic; }}
  .keywords {{ font-size: 10pt; margin-bottom: 12px; font-style: italic; }}
  .content {{ column-count: 2; column-gap: 0.25in; }}
  .section {{ margin-bottom: 0; }}
  .section h2 {{ font-size: 10pt; font-variant: small-caps; font-weight: bold; text-align: center; margin: 12pt 0 6pt 0; font-family: "Times New Roman", Times, serif; letter-spacing: 0.5pt; }}
  .section h3 {{ font-size: 10pt; font-style: italic; font-weight: normal; text-align: left; margin: 9pt 0 3pt 0; font-family: "Times New Roman", Times, serif; }}
  .section p {{ text-align: justify; text-indent: 0.17in; margin-bottom: 0; line-height: 1.15; }}
  .caption {{ font-size: 10pt; font-variant: small-caps; text-align: left; margin: 6pt 0; font-family: "Times New Roman", Times, serif; }}
  table.ieee-table {{ border-collapse: collapse; width: 100%; font-size: 9pt; margin: 8px 0; }}
  table.ieee-table th, table.ieee-table td {{ border: 0.5pt solid black; padding: 3px 6px; text-align: center; }}
  .tablehead {{ font-variant: small-caps; font-weight: bold; }}
  .tabletext {{ text-align: left; }}
  .references {{ margin-top: 12px; }}
  .references h2 {{ font-size: 10pt; font-variant: small-caps; font-weight: bold; text-align: center; margin: 12pt 0 6pt 0; font-family: "Times New Roman", Times, serif; }}
  .references p {{ font-size: 9pt; margin-left: 0.25in; text-indent: -0.25in; line-height: 1.15; margin-bottom: 6pt; text-align: left; }}
  @media print {{ body {{ padding: 0; }} }}
</style></head><body>
<div class="paper">
  <h1>{title}</h1>
  <div class="authors">{authors_html}</div>
  <div class="abstract"><span class="abstract-label">Abstract - </span><p>{abstract}</p></div>
  <div class="keywords"><span class="kw-label">Index Terms - </span>{keywords_str}</div>
  <div class="content">{sections_html}</div>
  {refs_html}
</div>
</body></html>"""

def extract_text(file_path: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.pdf':
        text = ""
        with open(file_path, 'rb') as f:
            for page in PyPDF2.PdfReader(f).pages:
                text += page.extract_text() + "\n"
        return text
    elif ext == '.docx':
        text = ""
        for para in Document(file_path).paragraphs:
            text += para.text + "\n"
        return text
    elif ext == '.ipynb':
        with open(file_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
        text = ""
        for cell in nb.get('cells', []):
            src = ''.join(cell.get('source', []))
            if cell.get('cell_type') == 'code':
                text += f"[code]\n{src}\n[/code]\n"
            else:
                text += src + "\n"
        return text
    elif ext == '.html' or ext == '.htm':
        from html.parser import HTMLParser
        class TagStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
            def handle_data(self, data):
                self.text.append(data)
        stripper = TagStripper()
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            stripper.feed(f.read())
        return ''.join(stripper.text)
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

@app.get("/")
async def root():
    return {"message": "Research Paper Generator", "status": "running"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    tmp = tempfile.mkdtemp()
    file_path = os.path.join(tmp, file.filename)
    with open(file_path, 'wb') as f:
        f.write(content)

    text = extract_text(file_path, file.filename)
    if not text.strip():
        raise HTTPException(400, "Could not extract text from file")

    analysis = analyze_document(text)
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "file_text": text, "filename": file.filename,
        "answers": {}, "questions_asked": [],
        "ready": False, "analysis": analysis,
        "paper_text": None
    }

    question = None
    if not analysis.get("ready", False):
        q_result = generate_question(text, {}, [], analysis)
        if not q_result.get("ready"):
            question = q_result

    if question and session_id in sessions:
        sessions[session_id]["_last_qtype"] = question.get("type", "")
    return {"session_id": session_id, "analysis": analysis, "question": question}

@app.post("/api/ask/{session_id}")
async def ask_question(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    q_result = generate_question(s["file_text"], s["answers"], s["questions_asked"], s.get("analysis"))
    if q_result.get("ready"):
        s["ready"] = True
        return {"ready": True}

    s["_last_qtype"] = q_result.get("type", "")
    return {"question": q_result["question"], "options": q_result.get("options", []), "context": q_result.get("context", ""), "type": q_result.get("type", "")}

@app.post("/api/answer/{session_id}")
async def submit_answer(session_id: str, data: dict):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    question = data.get("question", "")
    answer = data.get("answer", "")
    s["answers"][question] = answer
    s["questions_asked"].append(question)

    qtype = s.get("_last_qtype", "")

    if qtype in ("authors", "authors_confirm_no"):
        names = [n.strip() for n in answer.replace(",", ";").split(";") if n.strip()]
        if names:
            s["analysis"]["authors"] = names
        s["answers"]["_authors_ok"] = True
    elif qtype == "authors_confirm":
        if answer.lower().startswith("y"):
            s["answers"]["_authors_ok"] = True
        else:
            s["_last_qtype"] = "authors_confirm_no"
            return {
                "question": "Please type the correct author name(s), separated by semicolons.",
                "options": ["John Smith", "John Smith; Jane Doe"],
                "context": "Correct names for the paper byline.",
                "type": "authors_confirm_no"
            }
    elif qtype == "affiliation":
        if answer.strip():
            s["analysis"]["affiliation"] = answer.strip()
        s["answers"]["_affiliation_ok"] = True
    elif qtype == "email":
        if answer.strip():
            s["analysis"]["contact_email"] = answer.strip()
        s["answers"]["_email_ok"] = True
    elif qtype == "title":
        if answer.strip():
            s["analysis"]["title"] = answer.strip()
        s["answers"]["_title_ok"] = True
    elif qtype == "keywords":
        if answer.strip():
            kws = [k.strip() for k in answer.replace(";", ",").split(",") if k.strip()]
            s["analysis"]["keywords"] = kws
        s["answers"]["_keywords_ok"] = True
    elif qtype in ("title_confirm", "title_correct"):
        if qtype == "title_confirm" and not answer.lower().startswith("y"):
            s["_last_qtype"] = "title_correct"
            return {
                "question": "Please type the correct paper title.",
                "options": [s["analysis"].get("title", "")],
                "context": "The title at the top of the paper.",
                "type": "title_correct"
            }
        if qtype == "title_correct" and answer.strip():
            s["analysis"]["title"] = answer.strip()
        s["answers"]["_title_ok"] = True

    # ponytail: skip the extra clarity-gate LLM call — always advance
    q_result = generate_question(s["file_text"], s["answers"], s["questions_asked"], s.get("analysis"))
    if q_result.get("ready"):
        s["ready"] = True
        return {"ready": True}

    s["_last_qtype"] = q_result.get("type", "")
    return {"question": q_result["question"], "options": q_result.get("options", []), "context": q_result.get("context", ""), "type": q_result.get("type", "")}

def strip_reasoning(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if _heading_text(line):
            return "\n".join(lines[i:])
    return text

def _heading_text(line):
    stripped = line.strip()
    if not stripped or stripped.startswith("```") or stripped.startswith("==="):
        return None

    m = re.match(r'^(#{1,3})(\s*)(.*)', stripped)
    if m and (m.group(2) or not m.group(3) or len(m.group(1)) >= 2):
        return m.group(3).strip() or None

    for prefix in ["Abstract","Introduction","Literature","Related Work","Methodology",
                   "System Design","Implementation","Experimental","Results","Discussion",
                   "Conclusion","Future Work","References"]:
        clean = re.sub(r'^#+\s*', '', stripped)
        if clean.lower().startswith(prefix.lower()) and (clean.endswith(":") or len(clean) < len(prefix) + 5):
            return prefix

    return None

def parse_paper_text(paper_text, analysis, session_id):
    paper_text = strip_reasoning(paper_text)
    sections = []
    abstract = ""
    current_title = None
    current_content = []

    lines = paper_text.split("\n")
    md_title = None
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^#\s+\S', stripped) and not stripped.startswith("##"):
            md_title = stripped.lstrip("#").strip()
            start_idx = i + 1
        break

    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("```") or stripped.startswith("==="):
            continue
        heading = _heading_text(line)
        if heading:
            content = "\n".join(current_content).strip()
            if current_title:
                sections.append({"title": current_title, "content": content})
            else:
                abstract = content
            current_title = heading
            current_content = []
        else:
            current_content.append(line)

    if current_title:
        sections.append({"title": current_title, "content": "\n".join(current_content).strip()})
    else:
        abstract = "\n".join(current_content).strip()

    title = md_title or analysis.get("title", "Research Paper")

    abstract_section = None
    other_sections = []
    for sec in sections:
        if sec["title"].lower().startswith("abstract") or (sec["title"].lower() in ("abstract", "abstract.")):
            abstract_section = sec["content"]
        else:
            other_sections.append(sec)

    if not abstract_section and other_sections:
        intro = other_sections[0]["content"]
        abstract_section = intro[:500]

    authors = analysis.get("authors") or ["Author A", "Author B"]
    affiliation = analysis.get("affiliation") or analysis.get("domain") or "Engineering"
    contact_email = analysis.get("contact_email", "")
    authors_data = []
    for i, author in enumerate(authors):
        authors_data.append({"name": author, "affiliation": affiliation, "email": contact_email})

    refs = []
    for sec in other_sections[:]:
        if sec["title"].lower().startswith("reference"):
            raw = sec["content"]
            parts = re.split(r'\n\s*(?=\[\d+\])', raw.strip())
            for p in parts:
                p = p.strip()
                if p and re.match(r'\[\d+\]', p):
                    refs.append({"citation": re.sub(r'^\[\d+\]\s*', '', p)})
            other_sections.remove(sec)
    if not refs:
        refs = [
            {"citation": f"J. Smith, ``Advances in {analysis.get('domain', 'Technology')},'' IEEE Trans., vol. 45, no. 3, pp. 123-135, 2023."},
            {"citation": f"B. Johnson, ``Modern {analysis.get('domain', 'Technology')} Systems,'' IEEE Conf. Proc., pp. 456-467, 2022."},
            {"citation": f"C. Williams, ``{analysis.get('domain', 'Technology')} Innovation,'' IEEE J., vol. 12, no. 4, pp. 789-801, 2023."},
        ]

    html_content = generate_ieee_html(
        title=title,
        authors=authors_data,
        abstract=abstract_section or abstract or paper_text[:500],
        sections=other_sections,
        keywords=analysis.get("keywords", [analysis.get("domain", "Technology")]),
        domain=analysis.get("domain", "Technology"),
        references=refs
    )
    paper_json = {
        "title": title,
        "authors": authors_data,
        "abstract": abstract_section or abstract or "",
        "keywords": analysis.get("keywords", [analysis.get("domain", "Technology")]),
        "sections": other_sections,
        "references": [r["citation"] for r in refs],
    }
    base_name = analysis.get('title', 'paper').replace(' ', '_')
    return {
        "paper_text": paper_text,
        "html_content": html_content,
        "download_html": f"/api/download/{session_id}/html",
        "filename_html": f"{base_name}.html",
        "paper_json": paper_json,
    }

@app.get("/api/generate-stream/{session_id}")
def generate_stream(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    def event_stream():
        paper_text = ""
        try:
            for token in generate_paper_stream(s["file_text"], s["answers"], s["analysis"]):
                paper_text += token
                safe = token.replace("\n", "\\n").replace("\r", "\\r")
                yield f"data: {json.dumps({'type': 'token', 'content': safe})}\n\n"

            s["paper_text"] = paper_text
            result = parse_paper_text(paper_text, s["analysis"], session_id)
            s["html_content"] = result["html_content"]
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

def generate_pdf_from_html(html_content: str) -> bytes:
    from fpdf import FPDF

    def extract_section(regex, html, group=1):
        m = re.search(regex, html, re.DOTALL)
        return m.group(group).strip() if m else ""

    title = extract_section(r'<h1>(.*?)</h1>', html_content)
    abstract = extract_section(r'abstract-label">(.*?)</span>\s*<p>(.*?)</p>', html_content, 2)
    keywords = extract_section(r'kw-label">.*?</span>(.*?)</div>', html_content)
    abstract = re.sub(r'<[^>]+>', '', abstract)
    keywords = re.sub(r'<[^>]+>', '', keywords)

    # Authors (name, affiliation, email)
    author_blocks = re.findall(r'<div class="author">(.*?)</div>', html_content, re.DOTALL)
    authors = []
    for ab in author_blocks:
        name = re.sub(r'<[^>]+>', '', re.split(r'<br>', ab)[0]).strip()
        affil = re.sub(r'<[^>]+>', '', extract_section(r'class="affil">(.*?)</span>', ab)).strip()
        email = re.sub(r'<[^>]+>', '', extract_section(r'class="email">(.*?)</span>', ab)).strip()
        if name:
            authors.append((name, affil, email))

    sections_raw = re.findall(r'<h2>(.*?)</h2>(.*?)(?=<h2>|<div class="references"|$)', html_content, re.DOTALL)
    sections = []
    for t, body in sections_raw:
        t_clean = re.sub(r'<[^>]+>', '', t).strip()
        ps = re.findall(r'<p>(.*?)</p>', body, re.DOTALL)
        content = '\n\n'.join(re.sub(r'<[^>]+>', '', p).strip().replace('<br>', '\n') for p in ps if p.strip())
        tables = []
        for tbl in re.findall(r'<table class="ieee-table">(.*?)</table>', body, re.DOTALL):
            heads = [re.sub(r'<[^>]+>', '', h).strip() for h in re.findall(r'<th class="tablehead">(.*?)</th>', tbl)]
            rows = []
            for tr in re.findall(r'<tr>(.*?)</tr>', tbl, re.DOTALL):
                cells = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td class="tabletext">(.*?)</td>', tr)]
                if cells:
                    rows.append(cells)
            if heads or rows:
                tables.append((heads, rows))
        if t_clean and (content or tables):
            sections.append((t_clean, content, tables))

    def ascii_safe(t):
        t = t.replace('\u2014', '--').replace('\u2013', '-')
        t = t.replace('\u2018', "'").replace('\u2019', "'")
        t = t.replace('\u201c', '"').replace('\u201d', '"')
        t = t.replace('\u00b2', '^2').replace('\u00b3', '^3')
        t = t.replace('\u00d7', 'x').replace('\u00f7', '/')
        return t.encode('ascii', 'replace').decode('ascii')
    sections = [(ascii_safe(t), ascii_safe(c), tables) for t, c, tables in sections]
    title = ascii_safe(title)
    abstract = ascii_safe(abstract)
    keywords = ascii_safe(keywords)
    authors = [(ascii_safe(n), ascii_safe(a), ascii_safe(e)) for n, a, e in authors]

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)

    ml = mr = 18
    mt = mb = 18
    pw = 210
    content_w = pw - ml - mr
    col_gap = 6
    col_w = (content_w - col_gap) / 2
    col_x = [ml, ml + col_w + col_gap]
    bottom = 297 - mb

    state = {"col": 0, "y": mt}

    def ensure(h):
        if state["y"] + h > bottom:
            if state["col"] == 0:
                state["col"] = 1
                state["y"] = mt
            else:
                pdf.add_page()
                state["col"] = 0
                state["y"] = mt

    def para_height(w, h, txt):
        pdf.set_font("Times", "", 10)
        lines = pdf.multi_cell(w, h, txt, dry_run=True, output="LINES")
        return len(lines) * h

    def draw_smallcaps(x, y, w, text, size, line_h, align="C"):
        # Build wrapped lines using mixed (small-caps) widths
        def cwidth(ch):
            pdf.set_font("Times", "", int(size * 0.72) if ch.islower() else size)
            return pdf.get_string_width(ch.upper())
        words = text.split()
        lines, cur, curw = [], [], 0
        sp = pdf.get_string_width(" ")
        for word in words:
            ww = sum(cwidth(ch) for ch in word)
            if cur and curw + sp + ww > w:
                lines.append(" ".join(cur))
                cur, curw = [word], ww
            else:
                if cur:
                    curw += sp
                cur.append(word)
                curw += ww
        if cur:
            lines.append(" ".join(cur))
        for li, line in enumerate(lines):
            yy = y + li * line_h
            total = sum(cwidth(ch) if ch != " " else sp for ch in line)
            sx = x + (w - total) / 2 if align == "C" else x
            pdf.set_xy(sx, yy)
            for ch in line:
                if ch == " ":
                    pdf.set_font("Times", "", size)
                    pdf.cell(sp, line_h, " ", new_x="RIGHT", new_y="TOP")
                    continue
                pdf.set_font("Times", "", int(size * 0.72) if ch.islower() else size)
                wc = pdf.get_string_width(ch.upper())
                pdf.cell(wc, line_h, ch.upper(), new_x="RIGHT", new_y="TOP")
        pdf.set_font("Times", "", size)
        return len(lines)

    pdf.add_page()

    # --- Title block (full width, single column) ---
    pdf.set_font("Times", "B", 20)
    pdf.set_xy(ml, state["y"])
    pdf.multi_cell(content_w, 9, title, align="C", new_x="LMARGIN", new_y="NEXT")
    state["y"] = pdf.get_y() + 3
    for name, affil, email in authors:
        pdf.set_xy(ml, state["y"])
        pdf.set_font("Times", "", 12)
        pdf.multi_cell(content_w, 6, name, align="C", new_x="LMARGIN", new_y="NEXT")
        state["y"] = pdf.get_y()
        if affil:
            pdf.set_xy(ml, state["y"])
            pdf.set_font("Times", "I", 10)
            pdf.multi_cell(content_w, 5, affil, align="C", new_x="LMARGIN", new_y="NEXT")
            state["y"] = pdf.get_y()
        if email:
            pdf.set_xy(ml, state["y"])
            pdf.set_font("Times", "", 10)
            pdf.multi_cell(content_w, 5, email, align="C", new_x="LMARGIN", new_y="NEXT")
            state["y"] = pdf.get_y()
    state["y"] += 3
    if abstract:
        pdf.set_xy(ml, state["y"])
        pdf.set_font("Times", "I", 10)
        pdf.multi_cell(content_w, 5, f"Abstract - {abstract}", align="J", new_x="LMARGIN", new_y="NEXT")
        state["y"] = pdf.get_y() + 2
    if keywords:
        pdf.set_xy(ml, state["y"])
        pdf.set_font("Times", "I", 10)
        pdf.multi_cell(content_w, 5, f"Index Terms - {keywords}", align="J", new_x="LMARGIN", new_y="NEXT")
        state["y"] = pdf.get_y() + 4

    # --- Body (two columns) ---
    for sec_title, sec_content, tables in sections:
        size, line_h = 10, 12
        n_lines = draw_smallcaps(col_x[state["col"]], state["y"], col_w, sec_title, size, line_h, "C")
        state["y"] += n_lines * line_h + 2

        for para in sec_content.split('\n'):
            para = para.strip()
            if not para:
                continue
            ph = para_height(col_w, 5, para)
            ensure(ph + 1)
            pdf.set_xy(col_x[state["col"]], state["y"])
            pdf.set_font("Times", "", 10)
            pdf.multi_cell(col_w, 5, para, align="J", new_x="LEFT", new_y="NEXT")
            state["y"] = pdf.get_y() + 1

        for heads, rows in tables:
            table_rows = ([heads] if heads else []) + rows
            for idx, row in enumerate(table_rows):
                line = " | ".join(row)
                rh = para_height(col_w, 5, line)
                ensure(rh + 1)
                pdf.set_xy(col_x[state["col"]], state["y"])
                pdf.set_font("Times", "B" if (heads and idx == 0) else "", 9)
                pdf.multi_cell(col_w, 5, line, align="L", new_x="LEFT", new_y="NEXT")
                state["y"] = pdf.get_y() + 1
            state["y"] += 2

    return bytes(pdf.output())

def build_markdown(title, abstract, sections, keywords, refs):
    parts = [f"## Abstract\n{abstract}"]
    for sec in sections:
        parts.append(f"## {sec.get('title', '')}\n{sec.get('content', '')}")
    ref_lines = ["## References"]
    for i, r in enumerate(refs, 1):
        r = (r or "").strip()
        ref_lines.append(r if r.startswith("[") else f"[{i}] {r}")
    return "\n\n".join(parts + ref_lines)


# ─── Resume helpers ───────────────────────────────────────────────────────────

def generate_resume_html(resume_data: dict) -> str:
    """Render a clean single-column resume HTML."""
    name = resume_data.get("name", "Your Name")
    email = resume_data.get("email", "")
    phone = resume_data.get("phone", "")
    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    contact_str = " &middot; ".join(contact_parts)

    sections_html = ""
    section_order = ["Summary", "Education", "Experience", "Skills", "Projects", "Certifications"]
    for section_name in section_order:
        items = resume_data.get(section_name.lower(), [])
        if not items:
            continue
        sections_html += f'<div class="section"><div class="section-title">{section_name}</div>'
        if section_name == "Summary":
            sections_html += f'<p>{items[0] if isinstance(items, list) else items}</p>'
        elif section_name == "Skills":
            sections_html += '<div class="skills">'
            for skill in items:
                sections_html += f'<span class="skill">{skill}</span>'
            sections_html += '</div>'
        elif section_name in ("Education", "Certifications"):
            for item in items:
                if isinstance(item, dict):
                    title = item.get("degree") or item.get("name") or item.get("text", "")
                    sections_html += f'<div class="item"><div class="item-title">{title}</div>'
                    if item.get("school"):
                        sections_html += f'<div class="item-subtitle">{item["school"]}</div>'
                    if item.get("year"):
                        sections_html += f'<div class="item-date">{item["year"]}</div>'
                    sections_html += '</div>'
                else:
                    sections_html += f'<div class="item"><p>{item}</p></div>'
        elif section_name == "Experience":
            for item in items:
                if isinstance(item, dict):
                    title = item.get("role") or item.get("title") or ""
                    sections_html += f'<div class="item"><div class="item-header"><span class="item-title">{title}</span>'
                    if item.get("dates"):
                        sections_html += f'<span class="item-date">{item["dates"]}</span>'
                    sections_html += '</div>'
                    if item.get("company"):
                        sections_html += f'<div class="item-subtitle">{item["company"]}</div>'
                    for bullet in item.get("bullets", []):
                        sections_html += f'<p>&bull; {bullet}</p>'
                    sections_html += '</div>'
                else:
                    sections_html += f'<div class="item"><p>{item}</p></div>'
        elif section_name == "Projects":
            for item in items:
                if isinstance(item, dict):
                    title = item.get("name") or item.get("title") or ""
                    sections_html += f'<div class="item"><div class="item-title">{title}</div>'
                    if item.get("description"):
                        sections_html += f'<p>{item["description"]}</p>'
                    for bullet in item.get("bullets", []):
                        sections_html += f'<p>&bull; {bullet}</p>'
                    sections_html += '</div>'
                else:
                    sections_html += f'<div class="item"><p>{item}</p></div>'
        sections_html += '</div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{name} - Resume</title>
<style>
  @page {{ size: letter; margin: 0.5in; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10pt; color: #333; line-height: 1.45; }}
  .resume {{ max-width: 7in; margin: 0 auto; padding: 0.4in; }}
  .header {{ text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 12px; margin-bottom: 16px; }}
  .name {{ font-size: 22pt; font-weight: bold; color: #2c3e50; margin-bottom: 4px; }}
  .contact {{ font-size: 9pt; color: #666; }}
  .section {{ margin-bottom: 14px; }}
  .section-title {{ font-size: 11pt; font-weight: bold; color: #2c3e50; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #bdc3c7; padding-bottom: 3px; margin-bottom: 8px; }}
  .item {{ margin-bottom: 10px; }}
  .item-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .item-title {{ font-weight: bold; font-size: 10pt; }}
  .item-date {{ font-style: italic; color: #666; font-size: 9pt; }}
  .item-subtitle {{ font-style: italic; color: #555; font-size: 9.5pt; margin-bottom: 2px; }}
  .item p {{ font-size: 9.5pt; margin-top: 2px; }}
  .skills {{ display: flex; flex-wrap: wrap; gap: 5px; }}
  .skill {{ background: #ecf0f1; padding: 3px 10px; border-radius: 3px; font-size: 9pt; color: #333; }}
  @media print {{ body {{ padding: 0; }} .resume {{ padding: 0; }} }}
</style></head><body>
<div class="resume">
  <div class="header">
    <div class="name">{name}</div>
    <div class="contact">{contact_str}</div>
  </div>
  {sections_html}
</div>
</body></html>"""


def parse_resume_text(resume_text: str) -> dict:
    """Parse a markdown resume into structured JSON."""
    result = {
        "name": "",
        "email": "",
        "phone": "",
        "summary": [],
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
        "certifications": [],
    }
    lines = resume_text.strip().split("\n")
    current_section = None
    current_item = None
    section_map = {
        "summary": "summary",
        "education": "education",
        "experience": "experience",
        "skills": "skills",
        "projects": "projects",
        "certifications": "certifications",
    }

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("```"):
            continue

        # H2 section heading
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            current_section = section_map.get(heading)
            current_item = None
            continue

        if current_section is None:
            continue

        if current_section == "summary":
            result["summary"].append(stripped)
        elif current_section == "skills":
            # Strip bullet points and markdown bold markers
            clean = stripped.lstrip("- ").lstrip("* ").strip()
            clean = clean.replace("**", "").replace("__", "").strip()
            if clean:
                result["skills"].append(clean)
        elif current_section in ("education", "certifications"):
            if stripped.startswith("- ") or stripped.startswith("* "):
                clean = stripped[2:].strip().replace("**", "").replace("__", "")
                result[current_section].append({"text": clean})
            elif stripped.startswith("**") or stripped.startswith("###"):
                clean = stripped.lstrip("#").strip().replace("**", "").replace("__", "").strip()
                result[current_section].append({"text": clean})
            else:
                result[current_section].append({"text": stripped.replace("**", "").replace("__", "")})
        elif current_section in ("experience", "projects"):
            if stripped.startswith("### ") or stripped.startswith("**"):
                title = stripped.lstrip("#").strip().replace("**", "").replace("__", "").strip()
                current_item = {"title": title, "bullets": []}
                result[current_section].append(current_item)
            elif stripped.startswith("- ") or stripped.startswith("* "):
                bullet = stripped[2:].strip().replace("**", "").replace("__", "")
                if current_item:
                    current_item["bullets"].append(bullet)
                else:
                    current_item = {"title": "", "bullets": [bullet]}
                    result[current_section].append(current_item)
            else:
                clean = stripped.replace("**", "").replace("__", "")
                if current_item:
                    current_item["bullets"].append(clean)
                else:
                    current_item = {"title": clean, "bullets": []}
                    result[current_section].append(current_item)

    # Flatten summary
    result["summary"] = " ".join(result["summary"]) if result["summary"] else ""

    # Try to extract name from first line if not in section
    if not result["name"] and lines:
        first = lines[0].strip()
        if not first.startswith("#") and not first.startswith("##"):
            result["name"] = first

    return result


def generate_resume_pdf(html_content: str) -> bytes:
    """Generate a single-column resume PDF from HTML."""
    from fpdf import FPDF

    def ascii_safe(t):
        t = t.replace('\u2014', '--').replace('\u2013', '-')
        t = t.replace('\u2018', "'").replace('\u2019', "'")
        t = t.replace('\u201c', '"').replace('\u201d', '"')
        t = t.replace('\u00b2', '^2').replace('\u00b3', '^3')
        t = t.replace('\u00d7', 'x').replace('\u00f7', '/')
        return t.encode('ascii', 'replace').decode('ascii')

    # Extract data from HTML
    def extract(regex, html, group=1):
        m = re.search(regex, html, re.DOTALL)
        return ascii_safe(m.group(group).strip()) if m else ""

    name = extract(r'class="name">(.*?)</div>', html_content)
    contact = extract(r'class="contact">(.*?)</div>', html_content)
    sections_raw = re.findall(r'<div class="section">(.*?)</div>\s*(?=<div class="section">|$)', html_content, re.DOTALL)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    ml = mr = 18
    pw = 210
    content_w = pw - ml - mr

    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(ml, 20)
    pdf.cell(content_w, 10, name, align="C", new_x="LMARGIN", new_y="NEXT")

    if contact:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(ml, pdf.get_y() + 2)
        pdf.cell(content_w, 5, contact, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    # Divider line
    pdf.set_draw_color(44, 62, 80)
    pdf.set_line_width(0.5)
    pdf.line(ml, pdf.get_y(), ml + content_w, pdf.get_y())
    pdf.ln(6)

    # Sections
    for section_html in sections_raw:
        # Section title
        sec_title_m = re.search(r'class="section-title">(.*?)</div>', section_html)
        if not sec_title_m:
            continue
        sec_title = ascii_safe(sec_title_m.group(1).strip())

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(content_w, 7, sec_title.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(189, 195, 199)
        pdf.set_line_width(0.3)
        pdf.line(ml, pdf.get_y(), ml + content_w, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(51, 51, 51)

        # Items
        items = re.findall(r'<div class="item">(.*?)</div>', section_html, re.DOTALL)
        if not items:
            # Summary or plain text
            text = re.sub(r'<[^>]+>', '', section_html)
            text = ascii_safe(text.strip())
            if text:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_x(ml)
                pdf.multi_cell(content_w, 5, text, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
            continue

        for item_html in items:
            title = extract(r'class="item-title">(.*?)</div>', item_html)
            subtitle = extract(r'class="item-subtitle">(.*?)</div>', item_html)
            date = extract(r'class="item-date">(.*?)</div>', item_html)
            bullets = re.findall(r'<p>(.*?)</p>', item_html)

            if title:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_x(ml)
                if date:
                    pdf.cell(content_w - 35, 5, title, new_x="LEFT", new_y="TOP")
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.cell(35, 5, date, align="R", new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.cell(content_w, 5, title, new_x="LMARGIN", new_y="NEXT")

            if subtitle:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_x(ml)
                pdf.cell(content_w, 4, ascii_safe(subtitle), new_x="LMARGIN", new_y="NEXT")

            for bullet in bullets:
                clean = ascii_safe(re.sub(r'<[^>]+>', '', bullet).strip())
                if clean.startswith("•") or clean.startswith("&bull;"):
                    clean = clean.lstrip("•&bull;").strip()
                elif clean.startswith("-"):
                    clean = clean.lstrip("-").strip()
                pdf.set_font("Helvetica", "", 9)
                pdf.set_x(ml + 3)
                pdf.multi_cell(content_w - 6, 4.5, f"• {clean}", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(1.5)

        pdf.ln(2)

    # Skills (special handling)
    skill_spans = re.findall(r'class="skill">(.*?)</span>', html_content)
    if skill_spans:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(content_w, 7, "SKILLS", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(189, 195, 199)
        pdf.line(ml, pdf.get_y(), ml + content_w, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(51, 51, 51)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(ml)
        skills_text = "  |  ".join(ascii_safe(s) for s in skill_spans)
        pdf.multi_cell(content_w, 5, skills_text, new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


@app.post("/api/set-mode/{session_id}")
async def set_mode(session_id: str, data: dict):
    """Set the session mode to 'resume' or 'ieee'. Returns first resume question if resume mode."""
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    mode = data.get("mode", "ieee")
    s["mode"] = mode

    if mode == "resume":
        # Run resume analysis
        resume_analysis = analyze_document_for_resume(s["file_text"])
        s["resume_analysis"] = resume_analysis
        s["resume_answers"] = {}
        s["resume_questions_asked"] = []
        s["resume_ready"] = False
        s["resume_text"] = None
        s["resume_html"] = None
        s["resume_data"] = None

        # Get first question
        q_result = generate_resume_question(
            s["file_text"], s["resume_answers"], s["resume_questions_asked"], resume_analysis
        )
        if q_result.get("ready"):
            s["resume_ready"] = True
            return {"mode": mode, "ready": True}
        s["_last_resume_qtype"] = q_result.get("type", "")
        return {"mode": mode, "ready": False, "question": q_result}

    return {"mode": mode, "ready": False}


@app.post("/api/ask-resume/{session_id}")
async def ask_resume_question(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    q_result = generate_resume_question(
        s["file_text"], s["resume_answers"], s["resume_questions_asked"], s.get("resume_analysis")
    )
    if q_result.get("ready"):
        s["resume_ready"] = True
        return {"ready": True}

    s["_last_resume_qtype"] = q_result.get("type", "")
    return {"question": q_result["question"], "options": q_result.get("options", []),
            "context": q_result.get("context", ""), "type": q_result.get("type", "")}


@app.post("/api/answer-resume/{session_id}")
async def submit_resume_answer(session_id: str, data: dict):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    question = data.get("question", "")
    answer = data.get("answer", "")
    s["resume_answers"][question] = answer
    s["resume_questions_asked"].append(question)

    qtype = s.get("_last_resume_qtype", "")

    # Handle structured fields
    if qtype in ("name", "name_confirm"):
        if answer.lower().startswith("y") and s.get("resume_analysis", {}).get("name"):
            pass  # keep analysis name from confirm
        else:
            # User typed a new name (or confirmed without "y" — still store it)
            name = answer.replace("Yes, that's correct", "").replace("No, I'll type my name", "").strip()
            if name:
                s["resume_analysis"]["name"] = name
        s["resume_answers"]["_name_ok"] = True

    elif qtype in ("email", "email_confirm"):
        if answer.lower().startswith("y") and s.get("resume_analysis", {}).get("email"):
            pass  # keep analysis email from confirm
        else:
            email = answer.replace("Yes, that's correct", "").replace("No, I'll type a different email", "").strip()
            if email:
                s["resume_analysis"]["email"] = email
        s["resume_answers"]["_email_ok"] = True

    elif qtype == "phone":
        phone = answer.strip()
        if phone and not phone.lower().startswith("n"):
            s["resume_analysis"]["phone"] = phone
        s["resume_answers"]["_phone_ok"] = True

    # Check if user said no more
    user_said_no = any(
        answer.lower().startswith("no") and any(w in question.lower() for w in ("more", "additional", "details"))
        for question in [question]
    )

    q_result = generate_resume_question(
        s["file_text"], s["resume_answers"], s["resume_questions_asked"], s.get("resume_analysis")
    )
    if q_result.get("ready"):
        s["resume_ready"] = True
        return {"ready": True}

    s["_last_resume_qtype"] = q_result.get("type", "")
    return {"question": q_result["question"], "options": q_result.get("options", []),
            "context": q_result.get("context", ""), "type": q_result.get("type", "")}


@app.get("/api/generate-resume-stream/{session_id}")
def generate_resume_stream_endpoint(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    def event_stream():
        resume_text = ""
        try:
            for token in generate_resume_stream(s["file_text"], s["resume_answers"], s.get("resume_analysis", {})):
                resume_text += token
                safe = token.replace("\n", "\\n").replace("\r", "\\r")
                yield f"data: {json.dumps({'type': 'token', 'content': safe})}\n\n"

            s["resume_text"] = resume_text
            resume_data = parse_resume_text(resume_text)
            if s.get("resume_analysis", {}).get("name"):
                resume_data["name"] = s["resume_analysis"]["name"]
            if s.get("resume_analysis", {}).get("email"):
                resume_data["email"] = s["resume_analysis"]["email"]
            if s.get("resume_analysis", {}).get("phone"):
                resume_data["phone"] = s["resume_analysis"]["phone"]

            html = generate_resume_html(resume_data)
            s["resume_html"] = html
            s["resume_data"] = resume_data

            result = {
                "resume_text": resume_text,
                "resume_html": html,
                "resume_data": resume_data,
                "download_html": f"/api/download-resume/{session_id}/html",
                "filename_html": f"{resume_data.get('name', 'Resume').replace(' ', '_')}_Resume.html",
            }
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/save-resume/{session_id}")
async def save_resume(session_id: str, data: dict):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    resume_text = data.get("resume_text", s.get("resume_text", ""))
    s["resume_text"] = resume_text
    resume_data = parse_resume_text(resume_text)
    # Overlay contact info from analysis
    if s.get("resume_analysis", {}).get("name"):
        resume_data["name"] = s["resume_analysis"]["name"]
    if s.get("resume_analysis", {}).get("email"):
        resume_data["email"] = s["resume_analysis"]["email"]
    if s.get("resume_analysis", {}).get("phone"):
        resume_data["phone"] = s["resume_analysis"]["phone"]

    html = generate_resume_html(resume_data)
    s["resume_html"] = html
    s["resume_data"] = resume_data

    return {
        "resume_text": resume_text,
        "resume_html": html,
        "resume_data": resume_data,
        "download_html": f"/api/download-resume/{session_id}/html",
        "filename_html": f"{resume_data.get('name', 'Resume').replace(' ', '_')}_Resume.html",
    }


@app.post("/api/edit-resume/{session_id}")
async def edit_resume_endpoint(session_id: str, data: dict):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    instruction = (data.get("instruction") or "").strip()
    if not instruction:
        raise HTTPException(400, "No instruction provided")

    current = s.get("resume_text") or ""
    if not current:
        raise HTTPException(400, "No resume to edit yet")

    edited = edit_resume(current, instruction)
    s["resume_text"] = edited
    resume_data = parse_resume_text(edited)
    if s.get("resume_analysis", {}).get("name"):
        resume_data["name"] = s["resume_analysis"]["name"]
    if s.get("resume_analysis", {}).get("email"):
        resume_data["email"] = s["resume_analysis"]["email"]
    if s.get("resume_analysis", {}).get("phone"):
        resume_data["phone"] = s["resume_analysis"]["phone"]

    html = generate_resume_html(resume_data)
    s["resume_html"] = html
    s["resume_data"] = resume_data

    return {
        "resume_text": edited,
        "resume_html": html,
        "resume_data": resume_data,
        "download_html": f"/api/download-resume/{session_id}/html",
        "filename_html": f"{resume_data.get('name', 'Resume').replace(' ', '_')}_Resume.html",
    }


@app.get("/api/download-resume/{session_id}/{fmt}")
async def download_resume(session_id: str, fmt: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    name = s.get("resume_data", {}).get("name", "Resume").replace(" ", "_")
    if fmt == "html" and s.get("resume_html"):
        return Response(content=s["resume_html"], media_type="text/html",
                        headers={"Content-Disposition": f"attachment; filename={name}_Resume.html"})
    if fmt == "pdf" and s.get("resume_html"):
        pdf_bytes = generate_resume_pdf(s["resume_html"])
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={name}_Resume.pdf"})
    raise HTTPException(404, "Format not found")


@app.post("/api/save/{session_id}")
async def save_paper(session_id: str, data: dict):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    pj = data.get("paper_json", {})
    title = pj.get("title", s["analysis"].get("title", "Research Paper"))
    authors = [
        {"name": a.get("name", ""), "affiliation": a.get("affiliation", ""), "email": a.get("email", "")}
        for a in pj.get("authors", [])
    ]
    abstract = pj.get("abstract", "")
    kw = pj.get("keywords", [])
    if isinstance(kw, str):
        kw = [k.strip() for k in kw.split(",") if k.strip()]
    sections = [{"title": sec.get("title", ""), "content": sec.get("content", "")} for sec in pj.get("sections", [])]
    refs = [{"citation": r} for r in pj.get("references", [])]
    html = generate_ieee_html(title, authors, abstract, sections, kw, s["analysis"].get("domain", "Technology"), refs)
    paper_text = build_markdown(title, abstract, sections, kw, [r["citation"] for r in refs])
    pj["title"] = title
    s["html_content"] = html
    s["paper_text"] = paper_text
    s["paper_json"] = pj
    s["analysis"]["title"] = title
    s["analysis"]["authors"] = authors
    s["analysis"]["keywords"] = kw
    base = title.replace(' ', '_')
    return {
        "paper_text": paper_text,
        "html_content": html,
        "download_html": f"/api/download/{session_id}/html",
        "filename_html": f"{base}.html",
        "paper_json": pj,
    }


@app.post("/api/edit/{session_id}")
async def edit_paper_endpoint(session_id: str, data: dict):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    instruction = (data.get("instruction") or "").strip()
    if not instruction:
        raise HTTPException(400, "No instruction provided")
    current = s.get("paper_text") or ""
    if not current:
        raise HTTPException(400, "No paper to edit yet")
    edited = edit_paper(current, instruction, s["analysis"].get("title", ""))
    s["paper_text"] = edited
    result = parse_paper_text(edited, s["analysis"], session_id)
    s["analysis"]["title"] = result["paper_json"].get("title", s["analysis"].get("title"))
    s["html_content"] = result["html_content"]
    s["paper_json"] = result.get("paper_json")
    return result


@app.get("/api/download/{session_id}/{fmt}")
async def download(session_id: str, fmt: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    base = s['analysis'].get('title', 'paper').replace(' ', '_')
    if fmt == "html" and s.get("html_content"):
        return Response(content=s["html_content"], media_type="text/html",
                        headers={"Content-Disposition": f"attachment; filename={base}.html"})
    if fmt == "pdf" and s.get("html_content"):
        pdf_bytes = generate_pdf_from_html(s["html_content"])
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={base}.pdf"})
    raise HTTPException(404, "Format not found")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
