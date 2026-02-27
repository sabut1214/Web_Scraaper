# Universal Async Web Scraping Platform - Architecture Specification

## Phase 1: Architecture Overview

### System Design Principles

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Web UI     │  │   CLI Tool   │  │   SDK        │  │   Webhook    │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY (FastAPI)                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  /scrape    │  /status/{job_id}    │  /results/{job_id}    │  /health   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
          │                                         │
          ▼                                         ▼
┌─────────────────────────────────┐    ┌───────────────────────────────────────────┐
│     TASK QUEUE (Redis + ARQ)    │    │         STATE MANAGEMENT                 │
│  ┌───────────────────────────┐  │    │  ┌─────────────────────────────────────┐  │
│  │  Queue: scrape_tasks      │  │    │  │  Job Status Tracking                │  │
│  │  - priority              │  │    │  │  - pending/running/completed/failed│  │
│  │  - retry_count           │  │    │  │  - progress percentage              │  │
│  │  - scheduled_at          │  │    │  │  - result URLs / extracted data     │  │
│  └───────────────────────────┘  │    │  └─────────────────────────────────────┘  │
└─────────────────────────────────┘    └───────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         WORKER POOL (Async Playwright)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Worker 1  │  │  Worker 2   │  │  Worker N   │  │  Worker N+1 │              │
│  │  Browser   │  │  Browser    │  │  Browser    │  │  Browser    │              │
│  │  Instance  │  │  Instance   │  │  Instance   │  │  Instance   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐    │
│  │                      STEALTH MIDDLEWARE                                  │    │
│  │  - User-Agent Rotation        - Proxy Rotation                          │    │
│  │  - WebDriver Detection Bypass - Canvas Fingerprint Randomization       │    │
│  │  - Timezone/Locale Spoofing   - WebGL Vendor Spoofing                   │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EXTRACTION PIPELINE                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐           │
│  │  HTML Cleaner    │───▶│  DOM Serializer │───▶│  LLM Extractor   │           │
│  │  - Remove JS     │    │  - Text content │    │  - OpenAI/Gemini │           │
│  │  - Remove CSS    │    │  - Structure    │    │  - JSON Schema   │           │
│  │  - Remove SVG    │    │  - Metadata     │    │  - Validation    │           │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. API Layer (`/api`)
- **FastAPI Application**: Main entry point for job submission and status checking
- **Endpoints**:
  - `POST /scrape` - Submit new scraping job
  - `GET /status/{job_id}` - Get job status
  - `GET /results/{job_id}` - Get extracted results
  - `GET /jobs` - List all jobs (with pagination)
  - `DELETE /jobs/{job_id}` - Cancel/delete job
  - `GET /health` - Health check endpoint

### 2. Task Queue (`/worker`)
- **ARQ Worker**: Async task worker with Redis backend
- **Task Functions**:
  - `scrape_url_task()` - Individual URL scraping
  - `scrape_batch_task()` - Batch URL scraping
  - `cleanup_task()` - Browser/process cleanup

### 3. Playwright Engine (`/engine`)
- **BrowserManager**: Manages browser pool lifecycle
- **PageScraper**: Core scraping logic with stealth
- **StealthMiddleware**: Anti-detection techniques

### 4. Extraction Layer (`/extraction`)
- **HTMLCleaner**: Strips unnecessary tags
- **LLMExtractor**: Structured data extraction
- **PromptTemplates**: LLM prompt management

### 5. Data Layer (`/schemas`)
- **Pydantic Models**: Request/response validation
- **Job States**: Enum for job lifecycle

---

## Directory Structure

```
web_scraper/
├── main.py                      # FastAPI application entry point
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── README.md                    # Documentation
│
├── api/                         # API layer
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── scrape.py            # Scrape endpoints
│   │   ├── jobs.py              # Job management endpoints
│   │   └── health.py             # Health check
│   └── dependencies/
│       ├── __init__.py
│       ├── queue.py             # Queue client dependencies
│       └── storage.py           # Redis storage dependencies
│
├── schemas/                     # Pydantic models
│   ├── __init__.py
│   ├── request.py               # Request schemas
│   ├── response.py              # Response schemas
│   ├── job.py                   # Job state models
│   └── extraction.py             # Extraction result models
│
├── worker/                      # ARQ worker
│   ├── __init__.py
│   ├── tasks.py                 # Task definitions
│   ├── config.py                # Worker configuration
│   └── pool.py                  # Worker pool management
│
├── engine/                      # Playwright scraping engine
│   ├── __init__.py
│   ├── browser_manager.py       # Browser lifecycle
│   ├── page_scraper.py          # Core scraping logic
│   ├── stealth/
│   │   ├── __init__.py
│   │   ├── middleware.py         # Stealth middleware
│   │   ├── user_agents.py        # UA rotation
│   │   ├── proxy_manager.py     # Proxy rotation
│   │   └── fingerprint.py       # Fingerprint spoofing
│   └── config.py                # Engine configuration
│
├── extraction/                  # AI extraction layer
│   ├── __init__.py
│   ├── cleaner.py               # HTML cleaner
│   ├── extractor.py             # LLM extractor
│   ├── prompts.py               # Prompt templates
│   └── validators.py            # Output validators
│
├── core/                        # Core utilities
│   ├── __init__.py
│   ├── redis.py                 # Redis client
│   ├── logger.py                # Logging setup
│   └── exceptions.py            # Custom exceptions
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── api/
│   ├── worker/
│   ├── engine/
│   └── extraction/
│
└── scripts/                     # Utility scripts
    ├── install_browsers.py      # Playwright browser install
    └── redis_init.py            # Redis initialization
```

---

## Data Flow

1. **Job Submission**:
   ```
   Client → POST /scrape → Validate Request → 
   Create Job (Redis) → Enqueue Task (Redis Queue) → Return job_id
   ```

2. **Task Processing**:
   ```
   Worker → Dequeue Task → Acquire Browser → 
   Apply Stealth → Navigate → Extract HTML → 
   Clean HTML → LLM Extract → Save Results → Release Browser
   ```

3. **Result Retrieval**:
   ```
   Client → GET /results/{job_id} → 
   Check Status → Return Extracted Data
   ```

---

## Configuration Schema

```yaml
# config.yaml structure
app:
  host: "0.0.0.0"
  port: 8000
  workers: 4

redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null

worker:
  concurrency: 10
  browser_instances: 5
  timeout: 30

stealth:
  user_agent_rotation: true
  proxy_rotation: false
  proxies: []

extraction:
  provider: "openai"  # or "anthropic", "gemini"
  model: "gpt-4o-mini"
  temperature: 0.0
  max_tokens: 4000
```

---

## Redis Data Structures

| Key Pattern | Type | Description |
|-------------|------|-------------|
| `job:{job_id}` | Hash | Job metadata and status |
| `job:{job_id}:results` | List | Extracted results |
| `queue:scrape_tasks` | List | Pending scrape tasks |
| `pool:available_browsers` | Set | Available browser instances |
| `proxy:available` | Set | Available proxy list |

---

## API Response Formats

### Job Submission Response
```json
{
  "job_id": "uuid-string",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "total_urls": 10,
  "completed": 0,
  "failed": 0,
  "progress": 0.0
}
```

### Job Result Response
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "results": [
    {
      "url": "https://example.com/page1",
      "data": { ... },
      "markdown": "# Page Title\n\nContent...",
      "extracted_at": "2024-01-15T10:31:00Z"
    }
  ],
  "summary": {
    "total": 10,
    "successful": 9,
    "failed": 1
  }
}
```
