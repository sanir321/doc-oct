# DocOct — AI Research Paper Generator

Generate IEEE-compliant research papers from review literature using AI. Produces HTML and PDF output matching the IEEE DOCX template.

## Features

- AI-powered paper generation from literature review prompts
- IEEE-compliant HTML output (two-column, Times New Roman, proper sectioning)
- PDF export via fpdf2 (no heavy LaTeX/TeXLive dependency)
- LaTeX export (IEEEtran format) for Overleaf
- Dark/light theme
- Profile setup (name, course, degree, year)

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Set `OPENCODE_ZEN_API_KEY` in your environment or `backend/config.py`.

## Tech Stack

- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** FastAPI, OpenCode Zen API (Nemotron-3-Ultra-Free)
- **Export:** fpdf2 (PDF), IEEEtran (LaTeX), custom HTML
