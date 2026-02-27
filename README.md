# Universal Async Web Scraping Platform

A high-performance, distributed web scraping tool capable of extracting clean, structured data (JSON/Markdown) from any modern website. Handles JavaScript-heavy SPAs, massive concurrency, and standard anti-bot mitigations.

## Features

- **Distributed Workers** - Async Playwright workers with Redis + ARQ task queue
- **Stealth Middleware** - User-agent rotation, proxy swapping, WebDriver detection bypass
- **Content Cleaner** - Strips `<script>`, `<style>`, `<SVG>` tags before LLM extraction
- **AI Extraction** - Structured JSON extraction via OpenAI, Anthropic, or Gemini
- **REST API** - Submit URLs, check status, retrieve results

## Tech Stack

- Python 3.12+
- FastAPI
- Async Playwright
- Redis + ARQ
- Pydantic
- OpenAI / Anthropic / Gemini

## Installation

```bash
# Clone and enter directory
git clone <repo-url>
cd web_scraper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Keys (at least one required for extraction)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Extraction
EXTRACTION_PROVIDER=openai
EXTRACTION_MODEL=gpt-4o-mini
```

## Running

**1. Start Redis:**
```bash
docker run -d -p 6379:6379 redis
```

**2. Start API:**
```bash
uvicorn main:app --reload
```

**3. Start Worker (separate terminal):**
```bash
python -m worker.tasks
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scrape` | Submit single URL |
| POST | `/scrape/batch` | Submit up to 1000 URLs |
| GET | `/scrape/status/{job_id}` | Get job status |
| GET | `/scrape/results/{job_id}` | Get extracted results |
| GET | `/jobs` | List all jobs |
| DELETE | `/jobs/{job_id}` | Delete job |
| GET | `/health` | Health check |

## Usage Examples

### Scrape a Single URL

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Batch Scrape

```bash
curl -X POST "http://localhost:8000/scrape/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/page1",
      "https://example.com/page2"
    ]
  }'
```

### With Extraction Schema

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "mode": "extraction",
    "extraction_schema": {
      "properties": {
        "title": {"type": "string"},
        "links": {"type": "array", "items": {"type": "string"}}
      }
    }
  }'
```

### Check Status

```bash
curl "http://localhost:8000/scrape/status/{job_id}"
```

### Get Results

```bash
curl "http://localhost:8000/scrape/results/{job_id}"
```

## Request Options

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Target URL (required) |
| `mode` | string | `html`, `markup`, `extraction`, `full` |
| `extraction_schema` | object | JSON Schema for LLM extraction |
| `extraction_prompt` | string | Custom instructions for LLM |
| `proxy` | object | Proxy configuration |
| `headers` | object | Custom HTTP headers |
| `wait_for` | string | CSS selector to wait for |
| `timeout` | int | Page load timeout (ms) |
| `priority` | int | Task priority (higher = first) |

## Architecture

```
Client → FastAPI → Redis Queue → ARQ Workers → Playwright → LLM Extraction
```

## License

MIT
