# IEEE Research Paper Generator

AI-powered system that converts review literature into IEEE-compliant, publication-ready research papers using RAG and LaTeX automation.

## Project Structure

```
├── frontend/          # React + Vite frontend
├── backend/           # FastAPI backend
└── docs/             # Documentation
```

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
cp .env.example .env
# Edit .env with your credentials
python main.py
```

## Tech Stack

- Frontend: React, Vite, Tailwind CSS
- Backend: FastAPI, LangChain, Gemini 3
- Database: Supabase (Postgres + pgvector)
- Formatting: LaTeX (IEEEtran)
