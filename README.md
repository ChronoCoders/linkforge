# LinkForge

LinkForge is a LinkedIn content intelligence platform. It ingests a profile's
posts, runs natural-language analysis over the content and its comments, trains
a per-profile engagement model, and produces data-driven recommendations for
future posts. It is built for professionals who publish technical content and
want to understand what drives engagement rather than guess.

The system exposes a FastAPI backend and a Streamlit dashboard, and stores
profiles, posts, and vector embeddings in PostgreSQL with the `pgvector`
extension.

## Capabilities

- Profile and post ingestion via a Playwright-based scraper with cookie-based
  authentication.
- Sentiment analysis (VADER) augmented with lexical dimensions tuned for
  technical discussion: a pragmatic/balanced score, a tribalism score, and a
  technical-depth score.
- Theme detection, theme-confidence scoring, and comment-driven polarization
  scoring across a fixed taxonomy (technical deep dive, personal story,
  critique, pragmatic balance, and others).
- 384-dimension sentence embeddings stored as `pgvector` columns for similarity
  queries.
- A scikit-learn engagement predictor (random forest) trained per request on a
  profile's history, producing an engagement estimate and a success probability
  expressed relative to the profile's own distribution.
- Next-post recommendations: suggested topic, tone, structure, and hook,
  derived from the profile's highest-performing content patterns.
- CSV and JSON export of analysis results from the dashboard.

## Architecture

The `app` package follows a layered, domain-driven structure. Dependencies
point inward toward the domain.

- `app/domain` — Entities (`Profile`, `Post`, `Analysis`) and repository
  interfaces. No framework or database imports.
- `app/application` — Use cases (`ScrapeAndAnalyzeUseCase`,
  `GetProfileInsightsUseCase`), coordinating services (`LinkedInService`,
  `RecommendationService`), and data transfer objects.
- `app/infrastructure` — Concrete implementations: SQLAlchemy models and
  repositories, the Playwright scraper, the analysis modules, and the embedding
  service.
- `app/api` — FastAPI routers, request and response schemas, and dependency
  wiring.

### Request flow

- Ingestion: `POST /profiles` runs `ScrapeAndAnalyzeUseCase`, which fetches the
  profile (returning a cached record on a repeat request unless a refresh is
  requested), scrapes recent posts, and persists each post with its sentiment,
  theme analysis, and embedding.
- Analytics: the `/analytics/*` endpoints route through a single
  `GetProfileInsightsUseCase`, which aggregates the profile's text and posts,
  runs the analyzers, trains the predictor, and assembles recommendations. Each
  endpoint projects a different view of the same response.
- Direct scrape: `POST /scraping/profile` returns raw scraped data without
  touching the database.

## Technology

- Python 3.11+
- FastAPI, Uvicorn
- Streamlit
- PostgreSQL 16 with pgvector
- SQLAlchemy 2.0 (async) and Alembic
- Playwright (Chromium)
- sentence-transformers, scikit-learn, vaderSentiment
- Pydantic and pydantic-settings

## Prerequisites

- Python 3.11 or later
- Docker (for the PostgreSQL/pgvector container)

## Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium
cp .env.example .env
```

Start the database and apply migrations:

```
docker compose up -d db
alembic upgrade head
```

Optionally load sample data (one profile and a set of example posts):

```
python scripts/seed.py
```

## Running

Backend (defaults to port 8000):

```
uvicorn app.main:app --reload
```

Frontend (defaults to port 8501):

```
streamlit run streamlit_app/app.py --server.port 8501
```

The dashboard reads the backend URL from the `STREAMLIT_API_BASE` environment
variable, defaulting to `http://localhost:8000`. To point it at a backend on a
different port:

```
STREAMLIT_API_BASE=http://localhost:8077 streamlit run streamlit_app/app.py --server.port 8501
```

The dashboard's sidebar provides navigation through the full workflow:
ingestion, analysis results, performance insights, next-post recommendations,
and historical trends. A cookie manager in the sidebar accepts LinkedIn session
cookies for the direct (non-persisted) scrape.

## Configuration

Configuration is loaded from environment variables (and an optional `.env`
file) via pydantic-settings. See `.env.example` for the full list. Key
variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | local `linkforge` database |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `PLAYWRIGHT_HEADLESS` | Run the scraper browser headless | `true` |
| `EMBEDDING_MODEL` | sentence-transformers model name | `all-MiniLM-L6-v2` |
| `API_HOST`, `API_PORT` | Backend bind address and port | `0.0.0.0`, `8000` |
| `STREAMLIT_API_BASE` | Backend URL used by the dashboard | `http://localhost:8000` |

The embedding dimension is fixed at 384 to match the `Vector(384)` columns in
the database schema. Changing `EMBEDDING_MODEL` to a model with a different
dimension requires a corresponding migration.

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Service health check |
| POST | `/profiles` | Ingest a profile and its recent posts |
| GET | `/profiles/{id}` | Retrieve a stored profile |
| GET | `/profiles` | List recent profiles |
| POST | `/scraping/profile` | Scrape a profile without persisting |
| POST | `/analytics/profile` | Sentiment, themes, polarization, and prediction |
| POST | `/analytics/recommendations` | Next-post plan and ML recommendations |
| POST | `/analytics/trends` | Per-post performance reports and trend data |
| POST | `/analytics/compare` | Compare selected posts |

Interactive API documentation is available at `/docs` when the backend is
running.

Example:

```
curl -X POST http://localhost:8000/profiles \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://www.linkedin.com/in/example"}'

curl -X POST http://localhost:8000/analytics/profile \
  -H "Content-Type: application/json" \
  -d '{"profile_id": 1, "include_posts": true}'
```

## Authentication and scraping

LinkedIn access is cookie-based; there is no username and password login flow.
Cookies are read from local sources only and are never stored in the database.
For persisted ingestion (`POST /profiles`), provide them via the
`LINKEDIN_SESSION_COOKIES` environment variable (a JSON array) or a local,
gitignored `cookies.json` file. For the direct, non-persisted scrape
(`POST /scraping/profile`), pass them in the request body or via the dashboard's
sidebar cookie manager. The scraper retries with exponential backoff on rate
limiting and re-authenticates on authentication errors. Because the scraper
depends on LinkedIn's page structure, selector changes upstream are the first
thing to check if scraped fields come back empty.

## Development

The project targets a strict quality bar. Linting, formatting, and type
checking:

```
ruff check .
black --check .
mypy app/ scripts/
```

Tests:

```
pytest
```

The repository tests are integration tests that run against PostgreSQL. They
provision and tear down a dedicated `linkforge_test` database on the configured
server, so the database container must be running.

## Project layout

```
app/
  api/             FastAPI routers, schemas, dependency wiring
  application/     use cases, services, DTOs
  domain/          entities and repository interfaces
  infrastructure/  database, scraping, analysis, embeddings
  core/            configuration, logging, exceptions
migrations/        Alembic environment and versioned migrations
scripts/           seed script
streamlit_app/     Streamlit dashboard
tests/             integration tests
```

## Logging

Logging is configured with loguru, writing to the console and to rotating files
under `logs/`.
