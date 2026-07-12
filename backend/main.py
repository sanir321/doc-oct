from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
import uvicorn
import os, re, uuid, tempfile, json
import PyPDF2
from docx import Document
from config import MAX_FILE_SIZE, UPLOAD_DIR
from services.llm_service import analyze_document, generate_question, check_answer_clear, generate_paper_stream


app = FastAPI(title="Research Paper Generator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

sessions = {}

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
            author_parts.append(
                f'<div class="author">{a["name"]}{sup}<br><span class="affil">{affil}</span></div>'
            )
        authors_html = "".join(author_parts)

    sections_html = "".join(
        f'<div class="section"><h2>{s["title"]}</h2><p>{s["content"].replace(chr(10), "<br>")}</p></div>'
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
  sup {{ font-size: 8pt; vertical-align: super; line-height: 1; }}
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
  table {{ border-collapse: collapse; width: 100%; font-size: 9pt; margin: 8px 0; }}
  th, td {{ border: 0.5pt solid black; padding: 3px 6px; text-align: center; }}
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

    clarity = check_answer_clear(s["file_text"], question, answer)
    if not clarity.get("clear"):
        return {"follow_up": clarity["follow_up"], "options": clarity.get("options", []), "needs_clarification": True}

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

    roman_numerals = {"I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV"}

    m = re.match(r'^(#{1,3})(\s*)(.*)', stripped)
    if m and (m.group(2) or not m.group(3) or len(m.group(1)) >= 2):
        return m.group(3).strip() or None

    for prefix in ["Abstract","Introduction","Literature","Related Work","Methodology",
                   "System Design","Implementation","Experimental","Results","Discussion",
                   "Conclusion","Future Work","References"]:
        clean = re.sub(r'^#+\s*', '', stripped)
        if clean.lower().startswith(prefix.lower()) and (clean.endswith(":") or len(clean) < len(prefix) + 5):
            return prefix

    rn_match = re.match(r'^(?:#+\s*)?([IVXLCDM]+)\.(\s|$)', stripped)
    if rn_match and rn_match.group(1) in roman_numerals:
        after = stripped[rn_match.end():].strip()
        return f"{rn_match.group(1)}. {after}" if after else f"{rn_match.group(1)}."

    num_match = re.match(r'^(?:#+\s*)?(\d+)\.(\s|$)', stripped)
    if num_match:
        after = stripped[num_match.end():].strip()
        return f"{num_match.group(1)}. {after}" if after else f"{num_match.group(1)}."

    return None

def parse_paper_text(paper_text, analysis, session_id):
    paper_text = strip_reasoning(paper_text)
    sections = []
    abstract = ""
    current_title = None
    current_content = []

    for line in paper_text.split("\n"):
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
    domain = analysis.get("domain") or "Engineering"
    authors_data = []
    for i, author in enumerate(authors):
        authors_data.append({"name": author, "affiliation": f"Department of {domain}"})

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
        domain=analysis.get("domain", "Technology"),
        references=refs
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

        def render_table(table_para, x_start, cy):
            nonlocal col, first_page
            lines = table_para.strip().split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            parsed_rows = []
            max_cols = 0
            for line in lines:
                if '|' not in line:
                    continue
                if re.match(r'^[\s\|\+\-\=]+$', line):
                    continue
                cells = [c.strip() for c in line.split('|')]
                if line.startswith('|'):
                    cells = cells[1:]
                if line.endswith('|'):
                    cells = cells[:-1]
                if cells:
                    max_cols = max(max_cols, len(cells))
                    parsed_rows.append(cells)
            if not parsed_rows or max_cols == 0:
                pdf.set_font("Times", "", 10)
                pdf.set_xy(x_start, cy)
                pdf.multi_cell(col_w, 5.5, table_para, align="J", new_x="LMARGIN", new_y="NEXT")
                return pdf.get_y()
            cell_w = max(10, col_w / max_cols)
            line_h = 5.5
            y = cy
            row_heights = []
            for row_idx, row in enumerate(parsed_rows):
                padded = row + [''] * (max_cols - len(row))
                max_h = 0
                for cell_text in padded:
                    tw = pdf.get_string_width(cell_text or "")
                    num_lines = max(1, int(tw / max(1, cell_w - 2)) + 1)
                    max_h = max(max_h, num_lines * line_h)
                max_h = max(max_h, line_h + 1)
                row_heights.append(max_h)
            pdf.set_line_width(0.2)
            pdf.set_draw_color(80, 80, 80)
            for row_idx, row in enumerate(parsed_rows):
                padded = row + [''] * (max_cols - len(row))
                rh = row_heights[row_idx]
                if y + rh > bh:
                    if col == 0:
                        col = 1
                        y = tm
                        pdf.set_xy(lm + col_w + gutter, y)
                    else:
                        pdf.add_page()
                        first_page = False
                        col = 0
                        y = tm
                        pdf.set_xy(lm, y)
                if row_idx == 0:
                    pdf.set_font("Times", "B", 9.5)
                else:
                    pdf.set_font("Times", "", 9.5)
                current_x = x_start
                for ci, cell_text in enumerate(padded):
                    cx = current_x + ci * cell_w
                    pdf.rect(cx, y, cell_w, rh)
                    pdf.set_xy(cx + 0.5, y + 0.5)
                    pdf.multi_cell(cell_w - 1, line_h, cell_text or "", align="L")
                y += rh
            return y

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
                x_start = lm + (col_w + gutter) * col
                if '|' in para:
                    pdf.set_xy(x_start, cy)
                    cy = render_table(para, x_start, cy)
                else:
                    pdf.set_font("Times", "", 10)
                    pdf.set_xy(x_start, cy)
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
