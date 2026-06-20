# 🌍 Agentic Carbon Tracker

AI-powered personal carbon footprint tracker — scan a receipt, get insights, accept quests.

## Project Structure

```
carbon-tracker/
├── backend/
│   ├── main.py          # FastAPI — async endpoints, Gemini integration
│   └── models.py        # Pydantic schemas (strict typed)
├── frontend/
│   └── app.py           # Streamlit dashboard
├── tests/
│   └── test_app.py      # pytest suite (all AI mocked)
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### 1. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure secrets
```bash
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY
```

### 3. Run backend
```bash
cd backend
uvicorn main:app --reload --port 8000
# API docs → http://localhost:8000/docs
```

### 4. Run frontend (new terminal)
```bash
cd frontend
streamlit run app.py
# Opens → http://localhost:8501
```

### 5. Run tests
```bash
pytest tests/ -v
# All Gemini calls are mocked — no live API needed
```

## No API Key?
App runs in **demo mode** automatically — uses hardcoded sample data so
you can explore the full UI without a Gemini key.

## Key Design Decisions

| Concern | Decision |
|---------|----------|
| Async AI calls | `generate_content_async` — never blocks FastAPI event loop |
| Security | File type + size validation before any processing |
| Error safety | All exceptions caught; `ErrorResponse` envelope never exposes tracebacks |
| Caching | `@st.cache_data(ttl=3600)` on static CO₂ conversions |
| A11y | Text labels + icons alongside colours; chart text fallbacks; semantic headers |
| Testing | Pydantic validation, unit + integration tests, all external calls mocked |
