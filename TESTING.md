# Testing Guide

This repository includes a deterministic unit/API test suite based on the current implementation.

## Install dependencies

```bash
python -m pip install -r tests/requirements.txt
```

Note: `tests/requirements.txt` includes `-r ../requirements.txt`, so root base dependencies are included automatically.

## Run tests

Run all tests:

```bash
pytest -v
```

Run only unit tests:

```bash
pytest tests/unit -v
```

Run only API-layer tests:

```bash
pytest tests/api -v
```

Run inside Docker (recommended for consistency with the repository service structure):

```bash
docker compose --profile test run --rm tests
```

## Coverage report

Generate a terminal coverage summary:

```bash
pytest -v --cov=. --cov-report=term-missing
```

Docker equivalent:

```bash
docker compose --profile test run --rm tests python -m pytest tests/unit -v --cov=. --cov-report=term-missing --cov-report=xml:tests/reports/coverage-unit.xml --cov-report=html:tests/reports/htmlcov-unit
```

Generate XML coverage output (useful for CI quality gates):

```bash
pytest -v --cov=. --cov-report=xml:tests/reports/coverage.xml
```

Generate an HTML coverage report:

```bash
pytest -v --cov=. --cov-report=html:tests/reports/htmlcov
```

Open `tests/reports/htmlcov/index.html` in a browser to review per-file coverage details.

## How a reviewer should validate this suite

1. Create and activate a clean virtual environment.
2. Install dependencies from tests/requirements.txt.
3. Run the full suite with `pytest -v`.
4. Confirm the final summary shows all tests passing.

Expected quick checks:

- Collected tests should be deterministic across runs.
- Docker is optional for tests; `docker compose --profile test run --rm tests` is supported.
- No external Veryfi/API credentials are required.
- No real `.env` values are required for test execution.

## Where to see test results

Primary source of truth:

- Pytest terminal summary (passed/failed/skipped/errors).

Recommended artifact outputs for formal validation:

```bash
pytest -v --junitxml=tests/reports/junit.xml
```

Coverage artifact output (optional):

```bash
pytest -v --cov=. --cov-report=xml:tests/reports/coverage.xml
```

PowerShell run log capture (optional):

```bash
pytest -v | Tee-Object -FilePath tests/reports/pytest-run.log
```

These files can be shared as evidence in CI/CD or manual QA reviews.

## Components covered

- Shared logger: logger.py
- Backend security: backend/security.py
- Backend pipeline orchestration: backend/services.py
- Backend DB dependency behavior: backend/database.py (get_db lifecycle)
- Backend API routes: backend/api.py
- OCR config loading: components/ocr/config.py
- OCR file utilities: components/ocr/file_utils.py
- OCR wrapper/service adapter: components/ocr/ocr.py
- OCR CLI logic: components/ocr/main.py
- OCR API route: components/ocr/api.py
- Extractor dynamic format: components/extractor/formats/dynamic_format.py
- Extractor parser: components/extractor/core/document_parser.py
- Extractor file handlers: components/extractor/utils/file_handler.py
- Extractor CLI logic: components/extractor/main.py
- Extractor API route: components/extractor/api.py
- Validator engine: components/validator/core/rule_engine.py
- Validator API route: components/validator/main.py
- Frontend utility functions: frontend/utils/pdf_renderer.py and frontend/utils/styles.py
- Limited frontend view logic: frontend/views/dashboard.py (_open_project)

## Components intentionally not tested as pure unit tests

- Visual behavior/layout of Streamlit UI pages.
- Docker Compose integration wiring as a runtime integration test.
- Real Veryfi API integration.
- End-to-end cross-service execution with real networked containers.

These are excluded to keep unit tests fast, deterministic, and runnable without external services.

## Why Veryfi, Docker Compose, and visual Streamlit checks are excluded

- Veryfi calls are external and credentialed; unit tests must not depend on network, real credentials, or external API availability.
- Docker Compose orchestration is an integration environment concern, not a unit-test concern.
- Streamlit visual rendering is better validated through manual QA or E2E/UI tests; unit tests focus on internal logic/state transitions.

## Mocking strategy

- External HTTP boundaries are mocked:
  - backend/services.py pipeline calls are mocked with respx/httpx.
  - backend/api.py processing path mocks run_pipeline.
  - frontend dashboard loading uses mocked httpx.
- OCR external provider is mocked:
  - components/ocr/ocr.py uses mocked Veryfi Client.
  - components/ocr/api.py uses mocked module-level ocr_service and cache helpers.
- Environment and dotenv behavior are monkeypatched for OCR config tests.

## Temporary SQLite strategy for backend API tests

- backend/api.py tests override the get_db dependency with a per-test temporary SQLite database created under pytest tmp_path.
- SQLAlchemy metadata is created against the temp DB engine in tests.
- UPLOADS_DIR is monkeypatched to a temp directory.
- No persistent DB under /app/data/backend_app.db is used by tests.

## File and fixture isolation

- tests/fixtures contains small synthetic OCR and extracted JSON samples.
- tmp_path is used for cache files, output files, uploaded PDFs, and test databases.
- No permanent files are written into repository runtime folders by tests.

## Minimal app-code change for testability

- logger.py now supports an optional environment variable LOG_DIR.
- If LOG_DIR is set, logs are written there; otherwise behavior is unchanged (defaults to repository logs/).
- tests/conftest.py sets LOG_DIR to a temporary directory so tests do not append runtime logs into repository files.
