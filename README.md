# LinkForge

Advanced LinkedIn analytics platform.

## Setup

1. Prerequisites: Python 3.11+, Docker

2. Environment
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

3. Database
```
docker compose up -d db
alembic upgrade head
```

4. Backend
```
uvicorn app.main:app --reload
```

5. Streamlit
```
streamlit run streamlit_app/app.py --server.port 8501
```

## API Examples

Create profile:
```
curl -X POST http://localhost:8000/profiles -d '{"linkedin_url":"..."}'
```

Analytics:
```
curl -X POST http://localhost:8000/analytics/profile -d '{"profile_id":1}'
```

Seed:
```
python scripts/seed.py
```

## Streamlit Workflow

Use sidebar navigation for full flow: ingestion, analysis, insights, recommendations.

## Logging

Configured with loguru to console and logs/ with rotation.
```