# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Japanese project that monitors and fetches official government bulletins (官報/Kanpo) from kanpo.go.jp. The project has two main components:

1. **GitHub Action** (`fetch_kanpo.py`) - A Python script that checks for daily Kanpo updates and can download PDFs
2. **Vercel API** (`api/` directory) - A FastAPI web service for serving Kanpo data via REST endpoints

## Key Architecture

### Core Components

- **`fetch_kanpo.py`** - Main scraping script that fetches Kanpo data from official government website
  - Uses BeautifulSoup for HTML parsing
  - Handles PDF downloads and metadata extraction
  - Generates markdown files with structured data in `kanpo/YYYY-MM-DD/` directories
  - Designed to run as GitHub Action but can be executed locally

- **`api/app/main.py`** - FastAPI application entry point
  - Configured for Vercel serverless deployment via `vercel.json`
  - Includes CORS middleware for public API access
  - Uses Jinja2 templates and static file serving
  - Root path configured as `/api` for Vercel routing

### Directory Structure

```
├── api/app/                 # FastAPI application
│   ├── api/                 # API route modules
│   ├── core/config.py       # Settings and configuration
│   ├── models/              # Data models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # Static assets
├── kanpo/YYYY-MM-DD/        # Generated Kanpo data by date
├── fetch_kanpo.py           # Main scraper script
└── action.yml               # GitHub Action definition
```

## Development Commands

### Local Development

**Set up Python environment:**
```bash
uv sync
```

**Run Kanpo fetcher locally:**
```bash
# Fetch today's Kanpo without downloading PDFs
uv run fetch_kanpo.py --dlpdf false

# Fetch specific date with PDF download
uv run fetch_kanpo.py --dlpdf true --date 2025-07-05

# Capture and display results
result=$(uv run fetch_kanpo.py --dlpdf false --date 2025-07-03)
echo $result
```

**Run FastAPI development server:**
```bash
cd api/app
uvicorn main:app --reload --port 8000
```

**Run tests:**
```bash
# All tests via pytest
uv run pytest

# Comprehensive test runner with multiple options
uv run python api/tests/run_tests.py

# Specific test types
uv run python api/tests/run_tests.py --unit          # Unit tests only
uv run python api/tests/run_tests.py --integration  # Integration tests only
uv run python api/tests/run_tests.py --quick        # Quick tests (no integration)
uv run python api/tests/run_tests.py --manual       # Manual API test (requires live server)
uv run python api/tests/run_tests.py --validate     # API structure validation
```

### Deployment

**Vercel deployment:**
- The `vercel.json` configuration routes all requests to `api/app/main.py`
- Maximum function duration is set to 60 seconds
- Deploy using `vercel` CLI or connect GitHub repository

## Cultural and Language Considerations

This project handles Japanese government data and requires cultural sensitivity:

- **Content Language**: All official data is in Japanese
- **Date Formats**: Uses Japanese standard YYYY-MM-DD format
- **Government Compliance**: Respects robots.txt and official website policies
- **Data Handling**: Processes official government publications with appropriate respect

## Security Configuration

The API implements multiple security layers:

- **API Key Authentication**: Bearer token required for PDF download endpoints
- **Domain Whitelist**: CORS restricted to approved domains only
- **Environment-based Security**: Development/production mode switching
- **Rate Limiting**: Built-in protection against abuse

### API Usage
```bash
# API request with authentication
curl -X POST http://localhost:8000/api/pdf/download \
  -H "Authorization: Bearer dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/document.pdf", "filename": "test.pdf"}'
```

### Important Patterns

1. **Time Zone Handling**: Always use Japan time (Asia/Tokyo) for date operations
2. **URL Construction**: Uses `urljoin()` for proper URL building from government website
3. **Error Handling**: Includes retry logic and proper logging for web scraping
4. **Data Structure**: Maintains structured JSON output for integration with other systems

## Configuration Files

- **`pyproject.toml`** - All dependencies managed via UV (production + development)
- **`vercel.json`** - Vercel deployment configuration with 60s timeout
- **`pytest.ini`** - Test configuration with pythonpath set to `api/app`
- **`api/.env`** - Environment variables for FastAPI configuration
- **`action.yml`** - GitHub Action inputs/outputs definition

## Data Output Format

The scraper generates:
- **PDF files**: Downloaded to `kanpo/YYYY-MM-DD/` directories
- **Markdown files**: `官報_YYYY-MM-DD.md` with structured metadata
- **JSON outputs**: Available via API endpoints for integration

Key data fields:
- `kanpo_found`: Boolean indicating if bulletin was found
- `pdf_infos`: Array of PDF metadata (URL, filename, title)
- `toc_infos`: Table of contents with structured hierarchical data