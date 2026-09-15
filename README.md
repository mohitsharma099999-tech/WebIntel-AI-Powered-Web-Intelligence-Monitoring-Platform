# 🔐 WebIntel — AI-Powered Web Intelligence & Monitoring Platform

<p align="center">
  <strong>A production-style web intelligence and monitoring platform built with Python.</strong>
</p>

<p align="center">
  Scrape • Monitor • Detect Changes • Extract Data • Analyze with AI
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED.svg" alt="Docker">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs Welcome">
</p>

---

## 📌 Overview

**WebIntel** is a scalable web intelligence and monitoring platform that combines traditional web scraping, browser automation, asynchronous task processing, persistent storage, change detection, and optional AI-powered data extraction.

The platform is designed for applications such as:

* 🌐 Web scraping
* 📊 Website monitoring
* 🔍 Competitive intelligence
* 📈 Price monitoring
* 📰 News aggregation
* 🏢 Job listing aggregation
* 🔬 Research automation
* 🤖 AI-powered structured data extraction
* 🛡️ Content and brand monitoring

WebIntel supports both traditional HTTP scraping and JavaScript-rendered websites through Playwright.

---

## ✨ Features

| Feature                       | Description                                                   |
| ----------------------------- | ------------------------------------------------------------- |
| 🌐 **HTTP Scraping**          | Fast scraping using Requests and BeautifulSoup/lxml           |
| 🎭 **Browser Scraping**       | JavaScript-rendered page extraction using Playwright          |
| 🕷️ **Scrapy Crawler**        | Scalable crawling with robots.txt support                     |
| 🚀 **FastAPI REST API**       | Modern API with automatically generated OpenAPI documentation |
| 🗄️ **PostgreSQL**            | Persistent storage using SQLAlchemy 2.0                       |
| ⚡ **Celery + Redis**          | Distributed asynchronous task processing                      |
| 📸 **Historical Snapshots**   | Store previous versions of scraped pages                      |
| 🔐 **SHA-256 Hashing**        | Generate deterministic content fingerprints                   |
| 🔍 **Change Detection**       | Detect modifications between page versions                    |
| 🤖 **AI Extraction**          | Optional LLM-based structured data extraction                 |
| 🐳 **Docker Compose**         | Run the complete development stack with Docker                |
| 🛡️ **SSRF Protection**       | Prevent requests to internal/private network resources        |
| 🔑 **API Key Authentication** | Protect API endpoints                                         |
| 🔄 **Alembic**                | Database schema migrations                                    |
| 🧪 **Pytest**                 | Automated testing for core functionality                      |

---

# 🏗️ Architecture

```text
                              ┌──────────────────┐
                              │      Client      │
                              │   curl / UI / API│
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │     FastAPI      │
                              │    REST API      │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │      Redis       │
                              │   Message Queue  │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │      Celery      │
                              │      Worker      │
                              └────────┬─────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │                           │
                         ▼                           ▼
                ┌─────────────────┐         ┌─────────────────┐
                │   HTTP Scraper  │         │    Playwright   │
                │ Requests + BS4  │         │ Browser Engine  │
                └────────┬────────┘         └────────┬────────┘
                         │                           │    sting.


                         └─────────────┬─────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Content Parser   │
                              │ & Normalization  │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │   SHA-256 Hash   │
                              │   Fingerprint    │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │   PostgreSQL     │
                              │ Pages & Snapshots│
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Change Detector  │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │  Optional AI     │
                              │    Extraction    │
                              └──────────────────┘
```

---

# 📂 Project Structure

```text
WebIntel/
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── scraper.py
│       ├── browser_pool.py
│       ├── ai_extractor.py
│       ├── change_detector.py
│       ├── tasks.py
│       ├── security.py
│       └── exceptions.py
│
├── crawler/
│   └── spiders/
│       └── generic.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_scraper.py
│   └── test_change_detector.py
│
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

# 🔄 How WebIntel Works

The scraping pipeline follows these stages:

### 1. Queue

A client submits a scraping request through the FastAPI endpoint.

```text
POST /api/scrape
        │    sting.


        ▼
      Redis
        │
        ▼
     Celery
```

### 2. Fetch

The Celery worker determines which scraping strategy to use:

```text
Static page
    ↓
Requests + BeautifulSoup/lxml
```

or:

```text
JavaScript page
    ↓
Playwright
```

### 3. Normalize

The retrieved page is processed and normalized before comparison.

### 4. Hash

A SHA-256 fingerprint is generated:

```text
Page Content
     ↓
SHA-256
     ↓
Content Hash
```

### 5. Store

The page and its snapshot are persisted in PostgreSQL.

### 6. Detect

The new hash is compared with the previous snapshot.

```text
Previous Hash
      │
      ▼
    Compare
      ▲
      │
Current Hash
      │
      ▼
Changed / Unchanged
```

### 7. Extract

When enabled, the AI extraction layer converts unstructured content into structured information.

---

# 🎬 Demo

## Start the Application

```bash
cp .env.example .env

docker compose build

docker compose up
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## 🚀 Queue a Scraping Job

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "use_browser": false
  }'
```

Example response:

```json
{
  "task_id": "a1b2c3d4-...",
  "status": "queued",
  "url": "https://example.com"
}
```

---

## 📄 List Scraped Pages

```bash
curl http://localhost:8000/api/pages
```

Example response:

```json
[
  {
    "id": 1,
    "url": "https://example.com",
    "title": "Example Domain",
    "hash": "3a7bd3e2360a3d29eea436fcfb7e44c7...",
    "scraped_at": "2025-01-15T10:45:00"
  }
]
```

---

## 🔍 View Detected Changes

```bash
curl http://localhost:8000/api/changes
```

Example:

```json
[
  {
    "page_id": 1,
    "detected_at": "2025-01-15T11:00:00",
    "diff_type": "content_modified"
  }
]
```

---

# 📦 Installation

## Option 1 — Docker

Docker is the recommended setup because PostgreSQL, Redis, API services, and workers can be managed together.

### Clone the repository

```bash
git clone https://github.com/mohitsharma099999-tech/WebIntel.git

cd WebIntel
```

### Create environment file

```bash
cp .env.example .env
```

### Build the containers

```bash
docker compose build
```

### Start the application

```bash
docker compose up
```

---

# 🐍 Option 2 — Local Development

### Clone the repository

```bash
git clone https://github.com/mohitsharma099999-tech/WebIntel.git

cd WebIntel
```

### Create a virtual environment

Linux/macOS:

```bash
python3 -m venv venv

source venv/bin/activate
```

Windows:

```powershell
python -m venv venv

venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

Development dependencies:

```bash
pip install -r requirements-dev.txt
```

### Install Playwright browser

```bash
playwright install chromium
```

---

# ✅ Requirements

* Python 3.12+
* Docker
* Docker Compose
* PostgreSQL
* Redis
* Internet access for permitted public web pages

Verify your installation:

```bash
python --version

docker --version

docker compose version
```

---

# ⚡ Quick Start

You can start the complete stack with:

```bash
cp .env.example .env

docker compose up -d
```

Check the API:

```bash
curl http://localhost:8000/
```

Open the interactive API documentation:

```text
http://localhost:8000/docs
```

Submit your first scraping job:

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "use_browser": false
  }'
```

---

# 📚 Usage

## 1. Static HTML Scraping

For traditional server-rendered pages:

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "use_browser": false
  }'
```

The HTTP scraper can use:

```text
Requests
   ↓    sting.


HTML
   ↓
BeautifulSoup / lxml
   ↓
Extracted Content
```

---

## 2. JavaScript-Rendered Scraping

For websites that require JavaScript:

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "use_browser": true
  }'
```

The browser-based pipeline uses Playwright.

---

## 3. Run the Scrapy Crawler

Navigate to the crawler directory:

```bash
cd crawler
```

Run the generic spider:

```bash
scrapy crawl generic -a start_url=https://example.com
```

The example spider is designed to respect robots.txt and use conservative crawling settings.

For large-scale crawling, consider adding:

* Domain restrictions
* URL normalization
* Duplicate filtering
* Retry policies
* Persistent crawl frontier
* Per-domain rate limiting

---

# 🛠️ API Reference

| Method | Endpoint          | Description             |
| ------ | ----------------- | ----------------------- |
| `GET`  | `/`               | Health/status endpoint  |
| `POST` | `/api/scrape`     | Queue a scraping task   |
| `GET`  | `/api/websites`   | List monitored websites |
| `GET`  | `/api/pages`      | List scraped pages      |
| `GET`  | `/api/pages/{id}` | Get a specific page     |
| `GET`  | `/api/changes`    | View detected changes   |

---

## List Pages

```bash
curl http://localhost:8000/api/pages
```

## Get a Specific Page

```bash
curl http://localhost:8000/api/pages/1
```

## View Changes

```bash
curl http://localhost:8000/api/changes
```

---

# 🤖 AI-Powered Extraction

WebIntel includes an optional LLM extraction layer.

Configure your API key in `.env`:

```env
OPENAI_API_KEY=your_key_here
```

The AI layer can convert unstructured web content into structured information.

Example:

```json
{
  "job_title": "Python Developer",
  "company": "Example Technologies",
  "location": "Delhi",
  "skills": [
    "Python",
    "FastAPI",
    "PostgreSQL"
  ],
  "experience": "2 years"
}
```

### Recommended AI Pipeline

```text
Web Page
   ↓
Extract Text
   ↓
Clean / Normalize
   ↓
LLM
   ↓
Structured Output
   ↓
Schema Validation
   ↓
PostgreSQL
```

> ⚠️ Never blindly trust LLM-generated data. Validate model output against an explicit schema before storing or using it.

---

# 💡 Use Cases

### 📈 Price Monitoring

Monitor product pages and detect changes in:

* Price
* Availability
* Product information
* Promotions

### 📰 News Aggregation

Collect articles from permitted sources and process:

* Titles
* Authors
* Publication dates
* Content
* Categories

### 🔍 Competitive Intelligence

Monitor publicly accessible competitor pages and detect meaningful changes.

### 🏢 Job Board Monitoring

Extract structured job information:

```text
Job Title
Company
Location
Skills
Experience
Salary
```

### 🔬 Research Automation

Collect and organize publicly accessible research information.

### 🛡️ Brand Monitoring

Monitor permitted public pages for mentions and content changes.

### 📊 Content Auditing

Monitor websites you own or are authorized to audit.

---

# 🔒 Security

WebIntel is designed with security considerations for web-facing scraping infrastructure.

### 🛡️ SSRF Protection

The application should prevent requests to private and internal network destinations.

Examples include:

```text
127.0.0.1
localhost
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
169.254.169.254
::1
```

### 🔑 API Authentication

Production deployments should protect sensitive API endpoints with API-key authentication or another appropriate authentication mechanism.

### 🤖 AI Output Validation

Never assume that model output is trustworthy.

Validate AI-generated data against application schemas.

### 🔐 Environment Secrets

Never commit real credentials:

```env
DATABASE_URL=...
REDIS_URL=...
OPENAI_API_KEY=...
API_KEY=...
```

Keep secrets inside `.env` or your deployment secret manager.

### ⏱️ Rate Limiting

Use conservative request rates and respect server-provided:

```text
Retry-After
```

headers.

---

# ⚖️ Responsible Scraping

Only crawl content that you are permitted to access.

Respect:

* `robots.txt` directives where applicable
* Website Terms of Service
* Rate limits
* `Retry-After` headers
* Copyright restrictions
* Authentication boundaries
* Applicable laws and regulations

Do **not** use WebIntel to:

* Bypass CAPTCHAs
* Bypass authentication
* Circumvent access controls
* Bypass paywalls
* Defeat anti-bot mechanisms
* Access private systems
* Scrape content without appropriate authorization

Use the platform for legitimate research, monitoring, automation, and authorized data collection.

---

# 🧪 Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest tests/ -v
```

Example test structure:

```text
tests/
├── conftest.py
├── test_api.py
├── test_scraper.py
└── test_change_detector.py
```

When adding new functionality, add or update the corresponding tests.

---

# 🗄️ Database Migrations

WebIntel uses Alembic for database schema migrations.

Create a migration:

```bash
alembic revision --autogenerate -m "add new table"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback the latest migration:

```bash
alembic downgrade -1
```

---

# 🐳 Docker Services

The Docker environment is designed around the following components:

```text
┌───────────────────────────────┐
│           Docker              │
│                               │
│  ┌─────────┐   ┌───────────┐ │
│  │ FastAPI │   │  Celery   │ │
│  │   API   │   │  Worker   │ │
│  └────┬────┘   └─────┬─────┘ │
│       │               │       │
│       └───────┬───────┘       │
│               │               │
│        ┌──────▼──────┐        │
│        │    Redis    │        │
│        └─────────────┘        │
│                               │
│        ┌─────────────┐        │
│        │ PostgreSQL  │        │
│        └─────────────┘        │
│                               │
└───────────────────────────────┘
```

---

# 🗺️ Roadmap

## Infrastructure

* [ ] Crawl scheduler
* [ ] Persistent URL frontier
* [ ] URL canonicalization
* [ ] Duplicate URL detection
* [ ] Per-domain rate limiting    sting.


* [ ] Retry and failure queues

## Monitoring

* [ ] Website monitoring schedules
* [ ] HTML/text diff visualization
* [ ] Email alerts
* [ ] Slack notifications
* [ ] Webhook notifications

## Search

* [ ] OpenSearch / Elasticsearch integration
* [ ] Full-text search
* [ ] Semantic search
* [ ] Embeddings

## AI

* [ ] AI classification
* [ ] AI summarization
* [ ] Advanced structured extraction
* [ ] Semantic similarity detection

## Dashboard

* [ ] React dashboard
* [ ] Monitoring dashboard
* [ ] Historical change visualization
* [ ] Job management interface

## Observability

* [ ] Prometheus metrics
* [ ] Grafana dashboards
* [ ] Structured logging
* [ ] Distributed tracing

## DevOps

* [ ] CI/CD pipeline
* [ ] Automated security scanning
* [ ] Docker image optimization
* [ ] Automated test pipeline

---

# 🤝 Contributing

Contributions are welcome!

### 1. Fork the repository

```bash
git clone https://github.com/mohitsharma099999-tech/WebIntel.git
cd WebIntel
```

### 2. Create a feature branch

```bash
git checkout -b feature/amazing-feature
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

### 4. Make your changes

Follow:

* PEP 8
* Type hints
* Clear naming
* Small focused functions
* Appropriate error handling
* Test coverage

### 5. Run tests

```bash
pytest tests/ -v
```

### 6. Commit your changes

```bash
git add .

git commit -m "Add amazing feature"
```

### 7. Push your branch

```bash
git push origin feature/amazing-feature
```

### 8. Open a Pull Request

Please include a clear description of the change and update tests/documentation where appropriate.

---

# 📜 License

MIT License

Copyright (c) 2025 Mohit Sharma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

---

# ⭐ Support

If you find WebIntel useful:

* ⭐ Star the repository
* 🐛 Report bugs through GitHub Issues
* 💡 Suggest improvements
* 🔀 Submit pull requests
* 💬 Share the project with other developers

---

<div align="center">

### 🔐 WebIntel

**Built with 🐍 Python · FastAPI · Scrapy · Playwright · Celery · Redis · PostgreSQL**

MIT Licensed

[⬆ Back to Top](#-webintel--ai-powered-web-intelligence--monitoring-platform)

</div>
