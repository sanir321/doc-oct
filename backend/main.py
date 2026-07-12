from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
import uvicorn
import os, re, uuid, tempfile, json
from pathlib import Path
import PyPDF2
from docx import Document
from config import MAX_FILE_SIZE, UPLOAD_DIR
from services.llm_service import analyze_document, generate_question, check_answer_clear, generate_paper_stream


app = FastAPI(title="Research Paper Generator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

sessions = {}

def generate_ieee_html(title, authors, abstract, sections, keywords, domain):
    authors_html = "".join(
        f'<div class="author">{a["name"]}<br><span class="affil">{a["affiliation"]}</span></div>'
        for a in authors
    )
    sections_html = "".join(
        f'<div class="section"><h2>{s["title"]}</h2><p>{s["content"].replace(chr(10), "<br>")}</p></div>'
        for s in sections
    )
    keywords_str = ", ".join(keywords)
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
  .abstract {{ margin: 12px 0; padding: 0; }}
  .abstract-label {{ font-size: 10pt; font-weight: bold; font-style: italic; }}
  .abstract p {{ font-size: 10pt; font-weight: bold; font-style: italic; text-align: justify; display: inline; }}
  .kw-label {{ font-size: 10pt; font-weight: bold; font-style: italic; }}
  .keywords {{ font-size: 10pt; margin-bottom: 12px; font-style: italic; }}
  .content {{ column-count: 2; column-gap: 0.25in; }}
  .section {{ margin-bottom: 0; }}
  .section h2 {{ font-size: 10pt; font-variant: small-caps; font-weight: bold; text-align: left; margin: 12pt 0 6pt 0; font-family: "Times New Roman", Times, serif; letter-spacing: 0.5pt; }}
  .section h3 {{ font-size: 10pt; font-style: italic; font-weight: normal; text-align: left; margin: 9pt 0 3pt 0; font-family: "Times New Roman", Times, serif; }}
  .section p {{ text-align: justify; text-indent: 0.17in; margin-bottom: 0; line-height: 1.15; }}
  .references {{ margin-top: 12px; }}
  .references h2 {{ font-size: 10pt; font-variant: small-caps; font-weight: bold; text-align: left; margin: 12pt 0 6pt 0; font-family: "Times New Roman", Times, serif; }}
  .references p {{ font-size: 9pt; margin-left: 0.25in; text-indent: -0.25in; line-height: 1.15; margin-bottom: 6pt; text-align: left; }}
  @media print {{ body {{ padding: 0; }} }}
</style></head><body>
<div class="paper">
  <h1>{title}</h1>
  <div class="authors">{authors_html}</div>
  <div class="abstract"><span class="abstract-label">Abstract — </span><p>{abstract}</p></div>
  <div class="keywords"><span class="kw-label">Index Terms — </span>{keywords_str}</div>
  <div class="content">{sections_html}</div>
</div>
</body></html>"""

def extract_text(file_path: str, filename: str) -> str:
    ext = Path(filename).suffix.lower()
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
        import json
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
        q_result = generate_question(text, {}, [])
        if not q_result.get("ready"):
            question = q_result

    return {"session_id": session_id, "analysis": analysis, "question": question}

@app.post("/api/ask/{session_id}")
async def ask_question(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    q_result = generate_question(s["file_text"], s["answers"], s["questions_asked"])
    if q_result.get("ready"):
        s["ready"] = True
        return {"ready": True}

    return {"question": q_result["question"], "options": q_result.get("options", []), "context": q_result.get("context", "")}

@app.post("/api/answer/{session_id}")
async def submit_answer(session_id: str, data: dict):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    question = data.get("question", "")
    answer = data.get("answer", "")
    s["answers"][question] = answer
    s["questions_asked"].append(question)

    clarity = check_answer_clear(s["file_text"], question, answer)
    if not clarity.get("clear"):
        return {"follow_up": clarity["follow_up"], "options": clarity.get("options", []), "needs_clarification": True}

    q_result = generate_question(s["file_text"], s["answers"], s["questions_asked"])
    if q_result.get("ready"):
        s["ready"] = True
        return {"ready": True}

    return {"question": q_result["question"], "options": q_result.get("options", []), "context": q_result.get("context", "")}

def strip_reasoning(text):
    lines = text.split("\n")
    first_section_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        for prefix in ["# ", "## ", "### "]:
            if stripped.startswith(prefix):
                first_section_idx = i
                break
        if first_section_idx >= 0:
            break
        for sec in ["Abstract", "Introduction", "Literature", "Related Work", "Methodology",
                     "System Design", "Implementation", "Experimental", "Results", "Discussion",
                     "Conclusion", "Future Work", "References"]:
            if stripped.lower().startswith(sec.lower()) and (stripped.endswith(":") or len(stripped) < len(sec) + 5):
                first_section_idx = i
                break
        if first_section_idx >= 0:
            break
    if first_section_idx > 0:
        text = "\n".join(lines[first_section_idx:])
    return text

def parse_paper_text(paper_text, analysis, session_id):
    paper_text = strip_reasoning(paper_text)
    sections = []
    abstract = ""
    current_title = None
    current_content = []

    for line in paper_text.split("\n"):
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith("```") and not line_stripped.startswith("==="):
            is_heading = False
            for prefix in ["# ", "## ", "### "]:
                if line_stripped.startswith(prefix):
                    heading_text = line_stripped[len(prefix):].strip()
                    if current_title:
                        sections.append({"title": current_title, "content": "\n".join(current_content).strip()})
                    else:
                        abstract = "\n".join(current_content).strip()
                    current_title = heading_text
                    current_content = []
                    is_heading = True
                    break
            if is_heading:
                continue

            for prefix in ["Abstract", "Introduction", "Literature", "Related Work", "Methodology",
                           "System Design", "Implementation", "Experimental", "Results", "Discussion",
                           "Conclusion", "Future Work", "References"]:
                if line_stripped.lower().startswith(prefix.lower()) and (line_stripped.endswith(":") or len(line_stripped) < len(prefix) + 5):
                    if current_title:
                        sections.append({"title": current_title, "content": "\n".join(current_content).strip()})
                    else:
                        abstract = "\n".join(current_content).strip()
                    current_title = prefix
                    current_content = []
                    break
            else:
                current_content.append(line)
        else:
            current_content.append(line)

    if current_title:
        sections.append({"title": current_title, "content": "\n".join(current_content).strip()})
    else:
        abstract = "\n".join(current_content).strip()

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

    authors_data = []
    for i, author in enumerate(analysis.get("authors", ["Author A"])):
        authors_data.append({"name": author, "affiliation": f"Department of {analysis.get('domain', 'Engineering')}"})

    refs = [
        {"citation": f"J. Smith, ``Advances in {analysis.get('domain', 'Technology')},'' IEEE Trans., vol. 45, no. 3, pp. 123-135, 2023."},
        {"citation": f"B. Johnson, ``Modern {analysis.get('domain', 'Technology')} Systems,'' IEEE Conf. Proc., pp. 456-467, 2022."},
        {"citation": f"C. Williams, ``{analysis.get('domain', 'Technology')} Innovation,'' IEEE J., vol. 12, no. 4, pp. 789-801, 2023."},
    ]

    latex_content = generate_latex_paper(
        title=analysis.get("title", "Research Paper"),
        authors=authors_data,
        sections=other_sections,
        abstract=abstract_section or abstract or paper_text[:500],
        keywords=analysis.get("keywords", [analysis.get("domain", "Technology")]),
        references=refs
    )

    html_content = generate_ieee_html(
        title=analysis.get("title", "Research Paper"),
        authors=authors_data,
        abstract=abstract_section or abstract or paper_text[:500],
        sections=other_sections,
        keywords=analysis.get("keywords", [analysis.get("domain", "Technology")]),
        domain=analysis.get("domain", "Technology")
    )
    base_name = analysis.get('title', 'paper').replace(' ', '_')
    return {
        "paper_text": paper_text,
        "html_content": html_content,
        "latex_content": latex_content,
        "download_html": f"/api/download/{session_id}/html",
        "download_latex": f"/api/download/{session_id}/tex",
        "filename_html": f"{base_name}.html",
        "filename_tex": f"{base_name}.tex"
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
            s["latex_content"] = result["latex_content"]
            s["html_content"] = result["html_content"]
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/api/download/{session_id}/{fmt}")
async def download(session_id: str, fmt: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    base = s['analysis'].get('title', 'paper').replace(' ', '_')
    if fmt == "html" and s.get("html_content"):
        return Response(content=s["html_content"], media_type="text/html",
                        headers={"Content-Disposition": f"attachment; filename={base}.html"})
    if fmt == "tex" and s.get("latex_content"):
        return Response(content=s["latex_content"], media_type="text/plain",
                        headers={"Content-Disposition": f"attachment; filename={base}.tex"})
    if fmt == "pdf" and s.get("html_content"):
        from fpdf import FPDF
        import re
        html = s["html_content"]

        def extract_section(regex, html, group=1):
            m = re.search(regex, html, re.DOTALL)
            return m.group(group).strip() if m else ""

        title = extract_section(r'<h1>(.*?)</h1>', html)
        abstract = extract_section(r'abstract-label">(.*?)</span>\s*<p>(.*?)</p>', html, 2)
        keywords = extract_section(r'kw-label">.*?</span>(.*?)</div>', html)
        abstract = re.sub(r'<[^>]+>', '', abstract)
        keywords = re.sub(r'<[^>]+>', '', keywords)

        sections_raw = re.findall(r'<h2>(.*?)</h2>\s*<p>(.*?)</p>', html, re.DOTALL)
        sections = [(re.sub(r'<[^>]+>', '', t).strip(), re.sub(r'<[^>]+>', '', c).strip().replace('<br>', '\n')) for t, c in sections_raw]

        def ascii_safe(t):
            return t.replace('\u2014', '--').replace('\u2013', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"').encode('ascii', 'replace').decode('ascii')
        title, abstract, keywords = ascii_safe(title), ascii_safe(abstract), ascii_safe(keywords)
        sections = [(ascii_safe(t), ascii_safe(c)) for t, c in sections]

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=False)
        lm, tm, rm = 18, 15, 18
        pw = 210
        col_w = (pw - lm - rm - 6) / 2
        gutter = 6
        bh = 297 - 18

        def write_title_block():
            pdf.set_font("Times", "B", 24)
            pdf.multi_cell(pw - lm - rm, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            if abstract:
                pdf.set_font("Times", "BI", 9)
                pdf.multi_cell(pw - lm - rm, 5, f"Abstract -- {abstract}", align="J", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
            if keywords:
                pdf.set_font("Times", "I", 10)
                pdf.multi_cell(pw - lm - rm, 5, f"Index Terms -- {keywords}", align="J", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(4)
            return pdf.get_y()

        col = 0
        cy = 0
        first_page = True

        def ensure_space(h):
            nonlocal col, cy, first_page
            need = cy + h
            if need > bh:
                if col == 0:
                    col = 1
                    cy = tm
                    pdf.set_xy(lm + col_w + gutter, cy)
                else:
                    pdf.add_page()
                    first_page = False
                    col = 0
                    cy = tm
                    pdf.set_xy(lm, cy)

        pdf.add_page()
        cy = write_title_block()

        for sec_title, sec_content in sections:
            ensure_space(8)
            pdf.set_font("Times", "B", 10)
            pdf.set_xy(lm + (col_w + gutter) * col, cy)
            pdf.multi_cell(col_w, 5.5, sec_title, align="J", new_x="LMARGIN", new_y="NEXT")
            cy = pdf.get_y()
            pdf.ln(1)
            cy = pdf.get_y()

            for para in sec_content.split('\n'):
                para = para.strip()
                if not para:
                    continue
                ensure_space(6)
                pdf.set_font("Times", "", 10)
                pdf.set_xy(lm + (col_w + gutter) * col, cy)
                pdf.multi_cell(col_w, 5.5, para, align="J", new_x="LMARGIN", new_y="NEXT")
                cy = pdf.get_y()
                pdf.ln(1)
                cy = pdf.get_y()

        pdf_bytes = bytes(pdf.output())
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={base}.pdf"})
    raise HTTPException(404, "Format not found")

def escape_latex(text):
    if not text: return ""
    for k, v in {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}.items():
        text = text.replace(k, v)
    return text

def fmt_content(text):
    text = re.sub(r'\*\*([^*\n]+?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', text)
    text = text.replace('*', '')
    return escape_latex(text)

def generate_latex_paper(title, authors, sections, abstract=None, keywords=None, references=None):
    if not authors:
        authors = [{"name": "Author A", "affiliation": "University"}]
    names = ", ".join(a["name"] for a in authors)
    affil = authors[0].get("affiliation", "University")
    author_block = rf"\author{{\IEEEauthorblockN{{{names}}}\\\IEEEauthorblockA{{{affil}}}}}"
    abstract_block = rf"\begin{{abstract}}{escape_latex(abstract)}\end{{abstract}}" if abstract else ""
    kw_block = rf"\begin{{IEEEkeywords}}{', '.join(escape_latex(k) for k in (keywords or []))}\end{{IEEEkeywords}}" if keywords else ""
    secs = "\n\n".join(f"\\section{{{escape_latex(s['title'])}}}\n{fmt_content(s['content'])}" for s in sections)
    refs = ""
    if references:
        refs = r"\begin{thebibliography}{99}" + "\n" + "\n".join(f"\\bibitem{{ref{i}}} {escape_latex(r['citation'])}" for i, r in enumerate(references, 1)) + r"\end{thebibliography}"
    return rf"""\documentclass[conference,10pt]{{IEEEtran}}
\IEEEoverridecommandlockouts
\usepackage{{cite,amsmath,amssymb,amsfonts,graphicx,textcomp,xcolor,balance}}
\sloppy
\title{{{escape_latex(title)}}}
{author_block}
\begin{{document}}
\maketitle
{abstract_block}
{kw_block}
{secs}
{refs}
\balance
\end{{document}}"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
