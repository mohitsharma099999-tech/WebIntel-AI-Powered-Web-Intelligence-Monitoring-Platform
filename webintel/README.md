# WebIntel — AI-Powered Web Intelligence & Monitoring Platform

WebIntel is an advanced Python web-scraping platform designed as a production-style learning project. It combines Scrapy, Playwright, FastAPI, PostgreSQL, Redis, Celery, BeautifulSoup/lxml, Docker, and an optional LLM extraction layer.

## Features

- HTTP scraping with Requests + BeautifulSoup/lxml
- JavaScript-rendered scraping with Playwright
- Scrapy-based crawling
- FastAPI REST API
- PostgreSQL persistence
- Redis-backed Celery jobs
- Historical page snapshots
- SHA-256 content hashing
- Basic change detection
- Optional AI structured-data extraction
- Docker Compose development environment
- robots.txt compliance and conservative crawl settings

## Architecture

```text
Client
  |
  v
FastAPI
  |
  v
Redis Queue
  |
  v
Celery Worker
  |
  +--> Requests + BeautifulSoup
  |
  +--> Playwright
  |
  v
PostgreSQL
```

## Requirements

- Docker and Docker Compose
- Or Python 3.12+ for local development
- Internet access for permitted public web pages

## Run with Docker

```bash
cp .env.example .env
docker compose build
docker compose up
```

API:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

## Start a scraping job

```bash
curl -X POST http://localhost:8000/api/scrape   -H "Content-Type: application/json"   -d '{"url":"https://example.com","use_browser":false}'
```

For a JavaScript-rendered page:

```bash
curl -X POST http://localhost:8000/api/scrape   -H "Content-Type: application/json"   -d '{"url":"https://example.com","use_browser":true}'
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Health/status |
| POST | `/api/scrape` | Queue a scraping task |
| GET | `/api/websites` | List websites |
| GET | `/api/pages` | List scraped pages |
| GET | `/api/pages/{id}` | Get a page |
| GET | `/api/changes` | View detected changes |

## Run Scrapy

```bash
cd crawler
scrapy crawl generic -a start_url=https://example.com
```

The example spider obeys robots.txt and uses a conservative download delay. Extend it with domain restrictions, URL normalization, duplicate filtering, retry policies, and a persistent crawl frontier before using it for large crawls.

## Optional AI extraction

Set your API key in `.env`:

```text
OPENAI_API_KEY=your_key_here
```

Then use `backend/app/ai_extractor.py` to extract fields such as:

```json
{
  "job_title": "Python Developer",
  "company": "Example Technologies",
  "location": "Delhi",
  "skills": "Python, FastAPI, PostgreSQL",
  "experience": "2 years"
}
```

For production use, prefer structured model outputs and explicit validation rather than trusting raw model-generated JSON.

## Recommended next features

1. Crawl scheduler and URL frontier
2. URL canonicalization and duplicate detection
3. Per-domain rate limiting
4. Retry and failure queues
5. Database migrations with Alembic
6. User authentication and API keys
7. Website monitoring schedules
8. HTML/text diff visualization
9. OpenSearch/Elasticsearch indexing
10. React dashboard
11. Prometheus and Grafana metrics
12. Alerting via email/webhooks
13. AI classification and summarization
14. Embeddings and semantic search
15. Automated tests and CI/CD

## Responsible scraping

Only crawl content you are permitted to access. Respect robots.txt where applicable, website terms, rate limits, copyright restrictions, authentication boundaries, and applicable laws. Do not use this project to bypass CAPTCHAs, access controls, paywalls, or anti-bot mechanisms.

## License

Use and modify this project for learning and legitimate research. Check the terms of individual websites before crawling them.
