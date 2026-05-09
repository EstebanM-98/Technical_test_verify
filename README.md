# Smart Document Extractor

Smart Document Extractor is a Python-based document-processing application built around a microservice-style workflow:

1. A user uploads a PDF through a Streamlit interface.
2. The backend sends the file to an OCR service.
3. The OCR service uses the Veryfi Python SDK to extract raw OCR text.
4. The extractor service converts OCR text into structured JSON using configurable regex-based document formats.
5. The validator service checks extracted rows and document totals against configurable validation rules.
6. The frontend displays the PDF beside the extracted line items and allows the user to download the resulting JSON.

The current configured extraction format is `Switch Invoice`, defined in `components/extractor/configs/switch.json` and validated by `components/validator/configs/switch.json`.

Note: Some labels in the frontend refer to “bank statements”, but the current parser configuration targets Switch invoices. To process another document type, add a new extractor configuration and a matching validator configuration.

## Table of Contents

- [Main Features](#main-features)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Environment Variables](#environment-variables)
- [Installation and Execution with Docker Compose](#installation-and-execution-with-docker-compose)
- [Running Tests](#running-tests)
- [Testing Documentation](#testing-documentation)
- [Using the Web Interface](#using-the-web-interface)
- [Running Services Locally](#running-services-locally)
- [Running Individual Components](#running-individual-components)
- [API Reference](#api-reference)
- [Extraction Output Schema](#extraction-output-schema)
- [Adding a New Document Format](#adding-a-new-document-format)
- [Validation Rules](#validation-rules)
- [Detailed File and Function Reference](#detailed-file-and-function-reference)
- [Persistence and Generated Files](#persistence-and-generated-files)
- [Known Implementation Notes](#known-implementation-notes)
- [Troubleshooting](#troubleshooting)

## Main Features

- PDF upload through a Streamlit frontend.
- User registration and login through the backend.
- Project creation, editing, opening, and deletion.
- Veryfi OCR integration through the official `veryfi` Python package.
- Configurable extraction using JSON-defined regular expressions.
- Page-by-page extraction of line items.
- Validation of row-level calculations and document-level totals.
- Side-by-side PDF preview and editable line-item table in the interface.
- JSON download of extracted data.
- Docker Compose setup for running all services together.

## Architecture

The application is divided into five services:

```text
User browser
    |
    v
Frontend: Streamlit, port 8501
    |
    v
Backend: FastAPI, port 8000
    |
    |--> OCR service: FastAPI + Veryfi, port 8001
    |--> Extractor service: FastAPI + regex parser, port 8002
    |--> Validator service: FastAPI + rule engine, port 8003
    |
    v
SQLite database and uploaded PDFs stored under /app/data
```

The backend orchestrates the processing pipeline through `backend/services.py`:

```text
PDF file bytes
    -> OCR service /process
    -> Extractor service /extract
    -> Validator service /validate
    -> enriched JSON returned to frontend and stored in database
```

## Repository Structure

```text
Technical_test_verify-master/
├── .streamlit/
│   └── config.toml
├── backend/
│   ├── Dockerfile
│   ├── api.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   ├── schemas.py
│   ├── security.py
│   └── services.py
├── components/
│   ├── extractor/
│   │   ├── Dockerfile
│   │   ├── api.py
│   │   ├── configs/
│   │   │   └── switch.json
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── document_parser.py
│   │   ├── formats/
│   │   │   ├── __init__.py
│   │   │   ├── base_format.py
│   │   │   └── dynamic_format.py
│   │   ├── main.py
│   │   ├── output/
│   │   ├── requirements.txt
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_handler.py
│   ├── ocr/
│   │   ├── Dockerfile
│   │   ├── api.py
│   │   ├── config.py
│   │   ├── file_utils.py
│   │   ├── main.py
│   │   ├── ocr.py
│   │   ├── output/
│   │   └── requirements.txt
│   └── validator/
│       ├── Dockerfile
│       ├── configs/
│       │   └── switch.json
│       ├── core/
│       │   └── rule_engine.py
│       ├── main.py
│       └── requirements.txt
├── documents/
│   └── .gitkeep
├── frontend/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   ├── static/
│   │   └── logo.png
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── pdf_renderer.py
│   │   └── styles.py
│   └── views/
│       ├── __init__.py
│       ├── dashboard.py
│       ├── login.py
│       └── project.py
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── README.md
├── TESTING.md
├── requirements-dev.txt
├── requirements.txt
└── tests/
```

### Root Directory

| Path | Purpose |
|---|---|
| `.gitignore` | Excludes Python caches, virtual environments, `.env`, local documents, and generated OCR output. |
| `.streamlit/config.toml` | Defines the Streamlit theme and enables static serving. |
| `Dockerfile` | Root-level Dockerfile that installs root dependencies and runs the OCR CLI entrypoint by default. The multi-service application uses the service-specific Dockerfiles through `docker-compose.yml`. |
| `docker-compose.yml` | Starts OCR, extractor, validator, backend, and frontend services. |
| `requirements.txt` | Minimal root dependency file containing `veryfi` and `python-dotenv`. For the full application, each service has its own requirements file. |
| `requirements-dev.txt` | Development/testing dependencies used by the pytest suite. |
| `TESTING.md` | Detailed guide for test execution, scope, and validation artifacts. |
| `tests/` | Automated test suite organized by layer (`unit` and `api`), shared fixtures, and optional execution artifacts. |
| `documents/` | Placeholder folder for local documents. The `.gitignore` keeps the folder but ignores document contents. |

### Tests Directory

The `tests/` directory is structured to keep test execution deterministic, isolated from external services, and fast for local validation and CI.

| Path | Purpose |
|---|---|
| `tests/conftest.py` | Global pytest fixtures and setup helpers (temporary paths, fixture loaders, import-path setup). |
| `tests/fixtures/` | Static OCR/extraction payloads used as deterministic test inputs and expected structures. |
| `tests/unit/` | Unit tests for isolated logic (parsing, validation rules, frontend utilities, service helpers). |
| `tests/api/` | API-level tests for FastAPI routes and orchestration behavior with mocked dependencies. |
| `tests/reports/` | Optional generated artifacts such as `junit.xml` and execution logs when explicitly requested. |

### Backend Directory

The backend is the central FastAPI orchestration layer. It stores users, projects, uploaded PDFs, and extracted JSON.

| File | Purpose |
|---|---|
| `backend/api.py` | Defines authentication endpoints, project CRUD endpoints, PDF upload, pipeline execution, and PDF retrieval. |
| `backend/database.py` | Configures the SQLite database at `/app/data/backend_app.db`. |
| `backend/models.py` | Defines SQLAlchemy models for users and projects. |
| `backend/schemas.py` | Defines Pydantic request schemas. |
| `backend/security.py` | Provides password hashing and password verification. |
| `backend/services.py` | Calls OCR, extractor, and validator services in sequence. |
| `backend/Dockerfile` | Builds and runs the backend FastAPI service on port `8000`. |
| `backend/requirements.txt` | Backend dependencies. |

### OCR Component

The OCR service wraps Veryfi document processing.

| File | Purpose |
|---|---|
| `components/ocr/api.py` | FastAPI OCR service exposing `POST /process`. |
| `components/ocr/config.py` | Loads Veryfi credentials from `.env` or environment variables. |
| `components/ocr/file_utils.py` | Manages local OCR output folders and cached OCR text files for CLI usage. |
| `components/ocr/main.py` | CLI entrypoint for processing a single document file. |
| `components/ocr/ocr.py` | Defines the `VeryfiOCR` wrapper class. |
| `components/ocr/output/` | Default output folder for OCR text generated by CLI usage. |
| `components/ocr/Dockerfile` | Builds and runs the OCR FastAPI service on port `8001`. |
| `components/ocr/requirements.txt` | OCR service dependencies, including `veryfi`. |

### Extractor Component

The extractor converts OCR text into structured data using JSON-configured regex rules.

| File | Purpose |
|---|---|
| `components/extractor/api.py` | FastAPI extractor service exposing `POST /extract`. |
| `components/extractor/main.py` | CLI entrypoint for extracting structured JSON from a `.txt` file or raw text. |
| `components/extractor/configs/switch.json` | Current document-format configuration for Switch invoices. |
| `components/extractor/core/document_parser.py` | Loads available configs, selects the matching format, splits pages, and extracts header and line items. |
| `components/extractor/formats/base_format.py` | Abstract base interface for document formats. |
| `components/extractor/formats/dynamic_format.py` | Concrete parser built dynamically from JSON configuration. |
| `components/extractor/utils/file_handler.py` | Reads OCR text files and writes extracted JSON files. |
| `components/extractor/output/` | Contains generated and sample extraction outputs. |
| `components/extractor/Dockerfile` | Builds and runs the extractor FastAPI service on port `8002`. |
| `components/extractor/requirements.txt` | Extractor service dependencies. |

### Validator Component

The validator applies configurable consistency checks to extracted data.

| File | Purpose |
|---|---|
| `components/validator/main.py` | FastAPI validator service exposing `POST /validate`. |
| `components/validator/core/rule_engine.py` | Loads validation configs and evaluates rules. |
| `components/validator/configs/switch.json` | Validation rules for Switch invoices. |
| `components/validator/Dockerfile` | Builds and runs the validator FastAPI service on port `8003`. |
| `components/validator/requirements.txt` | Validator service dependencies. |

### Frontend Directory

The frontend is a Streamlit application used by end users.

| File | Purpose |
|---|---|
| `frontend/app.py` | Main Streamlit entrypoint. Initializes session state and routes between login, dashboard, and project views. |
| `frontend/views/login.py` | Login and registration screen. |
| `frontend/views/dashboard.py` | Project dashboard. Allows project creation, opening, renaming, and deletion. |
| `frontend/views/project.py` | PDF upload, processing trigger, extracted-data view, PDF preview, page navigation, line-item editor, validation display, and JSON download. |
| `frontend/utils/pdf_renderer.py` | Renders one PDF page as an image using PyMuPDF. |
| `frontend/utils/styles.py` | Injects custom CSS and displays the application logo. |
| `frontend/static/logo.png` | Logo used by the interface. |
| `frontend/Dockerfile` | Builds and runs the Streamlit app on port `8501`. |
| `frontend/requirements.txt` | Frontend dependencies. |

## Environment Variables

Create a `.env` file in the project root before running the application.

```env
VERYFI_CLIENT_ID=your_client_id
VERYFI_CLIENT_SECRET=your_client_secret
VERYFI_USERNAME=your_username
VERYFI_API_KEY=your_api_key
```

These variables are required by `components/ocr/config.py`. The OCR service will not start correctly without them.

The backend also requires service URLs. In Docker Compose they are already provided:

```env
OCR_URL=http://ocr:8001/process
EXTRACTOR_URL=http://extractor:8002/extract
VALIDATOR_URL=http://validator:8003/validate
```

The frontend requires the backend URL. In Docker Compose it is already provided:

```env
BACKEND_URL=http://backend:8000
```

For local development, set these variables manually before starting the backend and frontend.

## Installation and Execution with Docker Compose

Docker Compose is the recommended way to run this project because the backend stores data under `/app/data`, which matches the Docker container layout.

### Requirements

- Docker installed.
- Docker Compose available through `docker compose`.
- Valid Veryfi API credentials.

### Steps

1. Clone or extract the project.

```bash
cd Technical_test_verify-master
```

2. Create the `.env` file in the project root.

```bash
cat > .env <<'EOF'
VERYFI_CLIENT_ID=your_client_id
VERYFI_CLIENT_SECRET=your_client_secret
VERYFI_USERNAME=your_username
VERYFI_API_KEY=your_api_key
EOF
```

On Windows PowerShell, create the same file manually or run:

```powershell
@"
VERYFI_CLIENT_ID=your_client_id
VERYFI_CLIENT_SECRET=your_client_secret
VERYFI_USERNAME=your_username
VERYFI_API_KEY=your_api_key
"@ | Set-Content .env
```

3. Build and start all services.

```bash
docker compose up --build
```

4. Open the application in the browser.

```text
http://localhost:8501
```

5. Optional: open backend API documentation.

```text
http://localhost:8000/docs
```

6. Stop the application.

```bash
docker compose down
```

7. Stop and remove the persisted backend volume.

```bash
docker compose down -v
```

Use `docker compose down -v` only if you want to delete the SQLite database and uploaded PDFs stored in the Docker volume.

## Running Tests

The project includes a deterministic pytest suite for unit and API layers. These tests are designed to run without Docker Compose and without external network dependencies.

Install test dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Run all tests:

```bash
pytest -v
```

Run only unit tests:

```bash
pytest tests/unit -v
```

Run only API tests:

```bash
pytest tests/api -v
```

Optional validation artifacts:

```bash
pytest -v --junitxml=tests/reports/junit.xml
```

```powershell
pytest -v | Tee-Object -FilePath tests/reports/pytest-run.log
```

Notes:

- Test status should be read from pytest output and pytest artifacts, not application runtime logs.
- Tests isolate filesystem side effects using temporary paths and temporary database files.
- External APIs (Veryfi) and internal HTTP boundaries are mocked.

## Testing Documentation

For complete testing scope, fixture strategy, and reviewer checklist, see `TESTING.md`.

## Using the Web Interface

1. Open `http://localhost:8501`.
2. Register a new user in the `Register` tab.
3. Go to the `Login` tab and log in with the new user.
4. Create a project from the dashboard.
5. Open the project.
6. Upload a PDF document.
7. Click `Run (OCR + Extractor)`.
8. Review the extracted header fields and validation status.
9. Navigate through pages using the page controls.
10. Review or edit line items in the table.
11. Download the extracted JSON.

Important: Edits made in the Streamlit data editor are stored in the current Streamlit session and included when downloading JSON, but the current implementation does not persist those manual edits back to the backend database.

## Running Services Locally

Docker Compose is preferred. If you need local development without Docker, install each service dependency and run the services separately.

### Create a Virtual Environment

Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

From the project root:

```bash
pip install -r backend/requirements.txt
pip install -r components/ocr/requirements.txt
pip install -r components/extractor/requirements.txt
pip install -r components/validator/requirements.txt
pip install -r frontend/requirements.txt
```

### Set Python Import Path

Linux or macOS:

```bash
export PYTHONPATH=$PWD
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

### Start Each Service

Open one terminal per service.

OCR service:

```bash
uvicorn components.ocr.api:app --host 0.0.0.0 --port 8001
```

Extractor service:

```bash
uvicorn components.extractor.api:app --host 0.0.0.0 --port 8002
```

Validator service:

```bash
uvicorn components.validator.main:app --host 0.0.0.0 --port 8003
```

Backend service on Linux or macOS:

```bash
export OCR_URL=http://localhost:8001/process
export EXTRACTOR_URL=http://localhost:8002/extract
export VALIDATOR_URL=http://localhost:8003/validate
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

Backend service on Windows PowerShell:

```powershell
$env:OCR_URL = "http://localhost:8001/process"
$env:EXTRACTOR_URL = "http://localhost:8002/extract"
$env:VALIDATOR_URL = "http://localhost:8003/validate"
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

Frontend service on Linux or macOS:

```bash
export BACKEND_URL=http://localhost:8000
streamlit run frontend/app.py
```

Frontend service on Windows PowerShell:

```powershell
$env:BACKEND_URL = "http://localhost:8000"
streamlit run frontend/app.py
```

Local execution note: `backend/database.py` and `backend/api.py` use `/app/data` as the database and upload location. This works naturally inside Docker. For local execution, create that directory with write permissions on Unix-like systems, or change the paths in the backend code to a local project directory.

## Running Individual Components

### OCR CLI

The OCR CLI processes one document through Veryfi and saves OCR text under `components/ocr/output/<document_name>/<document_name>.txt`.

```bash
python components/ocr/main.py documents/example.pdf
```

If the document was already processed and the output text file exists, the CLI returns the existing file path instead of processing it again.

### Extractor CLI

The extractor CLI accepts either a `.txt` path or raw text.

```bash
python components/extractor/main.py components/ocr/output/example/example.txt
```

Custom output directory:

```bash
python components/extractor/main.py components/ocr/output/example/example.txt --output custom_output
```

The extractor writes JSON to:

```text
components/extractor/output/<file_name>/<file_name>.json
```

or to the directory passed with `--output`.

### Root Dockerfile

The root-level `Dockerfile` installs the root requirements and uses this entrypoint:

```text
python components/ocr/main.py
```

This image is useful for OCR CLI-style execution, but the full application uses `docker-compose.yml` and the service-specific Dockerfiles.

## API Reference

### Backend API, port 8000

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Register a user with username and password. |
| `POST` | `/auth/login` | Login and receive `user_id` and `username`. |
| `POST` | `/projects?user_id=<id>` | Create a project for a user. |
| `GET` | `/projects?user_id=<id>` | List projects for a user. |
| `GET` | `/projects/{project_id}` | Get project metadata and extracted JSON. |
| `PUT` | `/projects/{project_id}` | Rename a project. |
| `DELETE` | `/projects/{project_id}` | Delete a project and its stored PDF. |
| `POST` | `/projects/{project_id}/process` | Upload and process a PDF through OCR, extractor, and validator. |
| `GET` | `/projects/{project_id}/pdf` | Retrieve the stored PDF for a project. |

Example registration:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo"}'
```

Example login:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo"}'
```

Example project creation:

```bash
curl -X POST "http://localhost:8000/projects?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test project"}'
```

Example PDF processing:

```bash
curl -X POST http://localhost:8000/projects/1/process \
  -F "file=@documents/example.pdf;type=application/pdf"
```

### OCR API, port 8001

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/process` | Accepts a PDF upload and returns raw OCR text. |

Example:

```bash
curl -X POST http://localhost:8001/process \
  -F "file=@documents/example.pdf;type=application/pdf"
```

Expected response:

```json
{
  "ocr_text": "..."
}
```

### Extractor API, port 8002

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/extract` | Accepts OCR text and returns structured extracted data. |

Example:

```bash
curl -X POST http://localhost:8002/extract \
  -H "Content-Type: application/json" \
  -d '{"ocr_text":"Switch Dallas, TX ..."}'
```

### Validator API, port 8003

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/validate` | Accepts extracted data and returns validation status, errors, and details. |

Example:

```bash
curl -X POST http://localhost:8003/validate \
  -H "Content-Type: application/json" \
  -d '{"extracted_data":{"format":"Switch Invoice","header":{},"pages":[]}}'
```

## Extraction Output Schema

The extractor returns a dictionary with this structure:

```json
{
  "format": "Switch Invoice",
  "header": {
    "vendor_name": "Switch, Ltd.",
    "vendor_address": "Dallas, TX 75267-4592\nPO Box 674592",
    "invoice_date": "09/22/23",
    "due_date": "08/27/24",
    "invoice_number": "1556267",
    "bill_to_name": "Customer name",
    "total_amount": "1234.56",
    "currency": "USD"
  },
  "pages": [
    {
      "page_number": 1,
      "line_items_count": 1,
      "line_items": [
        {
          "description": "Service description",
          "quantity": 1.0,
          "rate": 100.0,
          "amount": 100.0
        }
      ]
    }
  ],
  "all_line_items": [
    {
      "description": "Service description",
      "quantity": 1.0,
      "rate": 100.0,
      "amount": 100.0
    }
  ],
  "validation": {
    "is_valid": true,
    "message": "Validated",
    "errors": [],
    "details": []
  }
}
```

The `validation` key is added by the backend after the validator service runs. The extractor service alone returns `format`, `header`, `pages`, and `all_line_items`.

## Adding a New Document Format

The extractor is designed to support new formats by adding JSON configuration files under:

```text
components/extractor/configs/
```

A format configuration has four main parts:

| Key | Meaning |
|---|---|
| `format_name` | Name returned in the extraction output. It must match the validator config name if validation is needed. |
| `signature_regex` | Regex used to detect whether the first page belongs to this format. |
| `header_fields` | Dictionary of fields to extract from the full OCR text. Supports `static` and `regex` rules. |
| `line_items` | Rules used to find and parse the line-item table. |

Example structure:

```json
{
  "format_name": "New Invoice Format",
  "signature_regex": "(?i)vendor name or unique text",
  "header_fields": {
    "vendor_name": {
      "type": "static",
      "value": "Vendor Name"
    },
    "invoice_number": {
      "type": "regex",
      "pattern": "Invoice No\\.\\s+(\\d+)",
      "group": 1
    }
  },
  "line_items": {
    "start_anchor": "Description\\s+Quantity\\s+Rate\\s+Amount",
    "stop_anchor": "^Total",
    "row_pattern": "^(.*?)\\s+([\\d,]+\\.\\d+)\\s+([\\d,]+\\.\\d+)\\s+([\\d,]+\\.\\d+)$",
    "columns": ["description", "quantity", "rate", "amount"]
  }
}
```

After adding the config, restart the extractor service.

Important parser behavior:

- The parser selects the first config whose `signature_regex` matches the first page.
- Pages are split using the form-feed character `\x0c`.
- Header fields are extracted from the full document text.
- Line items are extracted page by page.
- If a line does not match the row pattern but a row is already open, the line is appended to the first configured column, usually `description`.
- Columns named `quantity`, `rate`, and `amount` are converted to floats after removing commas.

## Validation Rules

Validation configurations are stored under:

```text
components/validator/configs/
```

The current validator config is `components/validator/configs/switch.json`.

It supports the following rule types in the current implementation.

### `row_math`

Checks each extracted row. The current implementation specifically computes:

```text
quantity * rate = amount
```

The configured `tolerance` controls the accepted numeric difference.

Current example:

```json
{
  "type": "row_math",
  "description": "Quantity * Rate = Amount",
  "expression": "quantity * rate",
  "equals": "amount",
  "tolerance": 0.1
}
```

Note: The fields `expression` and `equals` exist in the JSON config, but the current Python implementation directly uses `quantity`, `rate`, and `amount`.

### `document_sum`

Sums a numeric column across all extracted rows and compares it with a header field.

Current example:

```json
{
  "type": "document_sum",
  "description": "Sum of all amounts equals total_amount",
  "sum_column": "amount",
  "equals_header": "total_amount",
  "tolerance": 0.1
}
```

After adding or editing validation rules, restart the validator service.

## Detailed File and Function Reference

### `backend/api.py`

Creates the backend FastAPI application and database tables, then exposes authentication, project management, processing, and file-serving endpoints.

| Function | Description |
|---|---|
| `register(user, db)` | Creates a new user after checking that the username is not already registered. Hashes the password before storing it. |
| `login(user, db)` | Checks user credentials and returns the user ID and username. |
| `create_project(project, user_id, db)` | Creates a project associated with the given `user_id`. |
| `get_projects(user_id, db)` | Returns all projects owned by a user. |
| `get_project(project_id, db)` | Returns project metadata and parsed extracted JSON if available. |
| `update_project(project_id, project_update, db)` | Updates the project name. |
| `delete_project(project_id, db)` | Deletes the project record and removes the stored PDF if present. |
| `process_project(project_id, file, db)` | Saves the uploaded PDF, runs the full OCR-extractor-validator pipeline, stores the extracted JSON, and returns it. |
| `get_project_pdf(project_id)` | Returns the PDF stored for the project as a `FileResponse`. |

### `backend/database.py`

Configures the SQLAlchemy database.

| Function | Description |
|---|---|
| `get_db()` | Provides a database session to FastAPI endpoints and closes it after use. |

Important constants:

| Constant | Meaning |
|---|---|
| `SQLALCHEMY_DATABASE_URL` | SQLite URL pointing to `/app/data/backend_app.db`. |
| `engine` | SQLAlchemy engine. |
| `SessionLocal` | SQLAlchemy session factory. |
| `Base` | Declarative base used by SQLAlchemy models. |

### `backend/models.py`

Defines database tables.

| Class | Description |
|---|---|
| `User` | SQLAlchemy model for registered users. Fields: `id`, `username`, `hashed_password`. Relationship: `projects`. |
| `Project` | SQLAlchemy model for projects. Fields: `id`, `name`, `owner_id`, `extracted_data`, `pdf_filename`. Relationship: `owner`. |

### `backend/schemas.py`

Defines Pydantic request bodies.

| Class | Description |
|---|---|
| `UserCreate` | Request schema with `username` and `password`. Used for register and login. |
| `ProjectCreate` | Request schema with `name`. Used to create projects. |
| `ProjectUpdate` | Request schema with `name`. Used to rename projects. |

### `backend/security.py`

Handles password hashing.

| Function | Description |
|---|---|
| `hash_password(password)` | Returns a bcrypt hash for the provided password. |
| `verify_password(plain, hashed)` | Verifies a plaintext password against a bcrypt hash. If bcrypt verification raises `ValueError`, it falls back to direct plaintext comparison for backward compatibility. |

### `backend/services.py`

Runs the processing pipeline.

| Function | Description |
|---|---|
| `run_pipeline(filename, content)` | Asynchronously calls OCR, extractor, and validator services. Returns extracted data enriched with a `validation` key. Raises `RuntimeError` if required URLs are missing or a service fails. |

Pipeline details:

1. Reads `OCR_URL`, `EXTRACTOR_URL`, and `VALIDATOR_URL` from environment variables.
2. Sends the PDF bytes to the OCR service.
3. Sends OCR text to the extractor service.
4. Sends extracted JSON to the validator service.
5. Adds validation results to the extracted JSON.
6. Returns the enriched dictionary.

### `components/ocr/api.py`

Provides the OCR FastAPI service.

| Function | Description |
|---|---|
| `process_pdf(file)` | Receives an uploaded PDF, saves it temporarily, calls `VeryfiOCR.extract_ocr_text`, returns `ocr_text`, and deletes the temporary file. |

Initialization behavior:

- Loads Veryfi credentials using `load_configuration()`.
- Instantiates `VeryfiOCR` once at startup.
- If initialization fails, `/process` returns a `500` error.

### `components/ocr/config.py`

Loads Veryfi credentials.

| Function | Description |
|---|---|
| `load_configuration()` | Loads `.env` from the project root if present, falls back to default dotenv loading, validates required Veryfi keys, and returns a config dictionary. |

Required keys:

```text
VERYFI_CLIENT_ID
VERYFI_CLIENT_SECRET
VERYFI_USERNAME
VERYFI_API_KEY
```

### `components/ocr/file_utils.py`

Manages OCR output for CLI execution.

| Function | Description |
|---|---|
| `get_output_dir()` | Returns and creates, if necessary, `components/ocr/output`. |
| `check_if_processed(document_path)` | Checks whether OCR text already exists for a given document. Returns the existing text-file path or `False`. |
| `save_ocr_result(content, document_path)` | Saves OCR text to `components/ocr/output/<doc_name>/<doc_name>.txt` and returns the output path. |

### `components/ocr/main.py`

CLI entrypoint for OCR processing.

| Function | Description |
|---|---|
| `process_single_file(file_path, ocr_service)` | Validates that the input file exists, checks whether it was already processed, calls Veryfi OCR, saves OCR text, and returns the output path. |
| `main()` | Parses the CLI argument, loads configuration, initializes `VeryfiOCR`, and processes one file if provided. |

Usage:

```bash
python components/ocr/main.py documents/example.pdf
```

### `components/ocr/ocr.py`

Wraps the Veryfi SDK.

| Class or Method | Description |
|---|---|
| `VeryfiOCR` | Wrapper around the Veryfi `Client`. |
| `VeryfiOCR.__init__(config)` | Initializes the Veryfi client from `client_id`, `client_secret`, `username`, and `api_key`. |
| `VeryfiOCR.process_document(file_path)` | Sends a document to Veryfi and returns the full JSON response. Raises `RuntimeError` if the Veryfi call fails. |
| `VeryfiOCR.extract_ocr_text(file_path)` | Calls `process_document` and returns only the `ocr_text` field. Returns an empty string if the field is missing. |

### `components/extractor/api.py`

Provides the extractor FastAPI service.

| Class or Function | Description |
|---|---|
| `ExtractionRequest` | Pydantic model with one field: `ocr_text`. |
| `extract_data(request)` | Parses OCR text through `DocumentParser`. Returns extracted JSON or raises an HTTP error. |

### `components/extractor/main.py`

CLI entrypoint for extraction.

| Function | Description |
|---|---|
| `extract_information(input_source, output_dir=None)` | Accepts either a text-file path or raw text, runs `DocumentParser`, writes JSON output, and returns extracted data. |

Usage:

```bash
python components/extractor/main.py components/ocr/output/example/example.txt
```

### `components/extractor/core/document_parser.py`

Coordinates dynamic document-format extraction.

| Class or Method | Description |
|---|---|
| `DocumentParser` | Main parser class used by the API and CLI. |
| `DocumentParser.__init__()` | Initializes the parser and loads available JSON format configs. |
| `DocumentParser._load_configs()` | Reads all `.json` files from `components/extractor/configs` and creates a `DynamicFormat` parser for each one. |
| `DocumentParser._split_pages(text)` | Splits OCR text into pages using the form-feed character `\x0c`. Empty pages are discarded. |
| `DocumentParser.parse(text)` | Selects a matching format, extracts header fields from the full text, extracts line items per page, and returns structured data. Returns an error dictionary if the document is empty or no format matches. |

### `components/extractor/formats/base_format.py`

Defines the interface for document formats.

| Class or Method | Description |
|---|---|
| `BaseFormat` | Abstract base class for format parsers. |
| `BaseFormat.format_name` | Abstract property that returns the format name. |
| `BaseFormat.is_match(first_page_text)` | Abstract method that determines whether a document matches this format. |
| `BaseFormat.extract_header_fields(page_text)` | Abstract method for extracting header data. |
| `BaseFormat.extract_line_items(page_text)` | Abstract method for extracting line items. |

### `components/extractor/formats/dynamic_format.py`

Implements a configurable parser from JSON rules.

| Class or Method | Description |
|---|---|
| `DynamicFormat` | Parser built from one JSON configuration. |
| `DynamicFormat.__init__(config)` | Stores config data, format name, signature regex, header rules, and line-item rules. |
| `DynamicFormat.format_name` | Returns the configured format name. |
| `DynamicFormat.is_match(first_page_text)` | Uses `signature_regex` to decide whether this parser applies to the document. |
| `DynamicFormat.extract_header_fields(page_text)` | Applies `static` and `regex` header rules and returns extracted header fields. Missing regex matches are returned as `None`. |
| `DynamicFormat.extract_line_items(page_text)` | Uses table anchors and row regex to extract line items. Converts `quantity`, `rate`, and `amount` columns to floats. Appends overflow lines to the first column. |

### `components/extractor/utils/file_handler.py`

File helpers used by the extractor CLI.

| Function | Description |
|---|---|
| `read_text(file_path)` | Reads a UTF-8 text file and returns its content. |
| `write_json(data, file_path)` | Writes a dictionary as pretty-printed UTF-8 JSON with `ensure_ascii=False`. |

### `components/validator/main.py`

Provides the validator FastAPI service.

| Class or Function | Description |
|---|---|
| `ValidationRequest` | Pydantic model with one field: `extracted_data`. |
| `validate_document(req)` | Runs `ValidatorEngine.validate` and returns the validation result. |

### `components/validator/core/rule_engine.py`

Loads and executes validation rules.

| Class or Method | Description |
|---|---|
| `ValidatorEngine` | Validation engine used by the API. |
| `ValidatorEngine.__init__()` | Initializes the engine and loads validation configs. |
| `ValidatorEngine._load_configs()` | Reads all `.json` files from `components/validator/configs` and stores them by `format_name`. |
| `ValidatorEngine.validate(extracted_data)` | Finds the validation config for the extracted format, collects all line items, applies configured rules, and returns `is_valid`, `message`, `errors`, and `details`. |

### `frontend/app.py`

Main Streamlit application.

Primary responsibilities:

- Adds `frontend/` to `sys.path` so `views` and `utils` can be imported.
- Sets the Streamlit page configuration.
- Reads `BACKEND_URL` from the environment, defaulting to `http://localhost:8000`.
- Injects custom CSS.
- Initializes session state keys: `user`, `current_project`, `pdf_bytes`, `pdf_page`, and `extracted_data`.
- Routes the interface to login, dashboard, or project view depending on session state.

### `frontend/views/login.py`

Login and registration interface.

| Function | Description |
|---|---|
| `login_view(backend_url)` | Displays login and registration tabs. Calls backend `/auth/login` and `/auth/register`. Stores logged-in user data in Streamlit session state. |

### `frontend/views/dashboard.py`

Project dashboard interface.

| Function | Description |
|---|---|
| `dashboard_view(backend_url)` | Displays the sidebar, logout button, usage instructions, project creation tab, and project list. Supports opening, editing, and deleting projects. |
| `_open_project(project_id, backend_url)` | Loads selected project data and stored PDF from the backend, updates Streamlit session state, and routes to the project view. |

### `frontend/views/project.py`

Project upload and extraction interface.

| Function | Description |
|---|---|
| `project_view(backend_url)` | Displays the selected project. Routes either to the upload view or the result view depending on whether extracted data exists. |
| `_upload_view(project, backend_url)` | Lets the user upload a PDF and triggers backend processing through `/projects/{id}/process`. |
| `_result_view(project, backend_url)` | Displays validation, header fields, JSON download button, PDF preview, page navigation, and editable line items. |
| `_show_validation(data)` | Displays validation status, validation errors, and a downloadable validation log. |
| `_show_header(data)` | Displays main extracted header fields as Streamlit metrics. |

### `frontend/utils/pdf_renderer.py`

PDF preview helper.

| Function | Description |
|---|---|
| `display_pdf(pdf_bytes, page_number)` | Opens the PDF from bytes using PyMuPDF, renders the selected page as a PNG image, and displays it in Streamlit. |

### `frontend/utils/styles.py`

Frontend visual helpers.

| Function | Description |
|---|---|
| `inject_css()` | Injects custom CSS for buttons, download buttons, and data editor containers. |
| `display_logo(sidebar=False)` | Displays `frontend/static/logo.png` either in the sidebar or centered in the main layout. |

## Persistence and Generated Files

### Backend Persistence

The backend stores persistent data in:

```text
/app/data/backend_app.db
/app/data/uploads/project_<project_id>.pdf
```

In Docker Compose, this path is backed by the `backend_data` Docker volume:

```yaml
volumes:
  backend_data:
```

### OCR CLI Output

When using the OCR CLI, generated OCR text is stored under:

```text
components/ocr/output/<document_name>/<document_name>.txt
```

### Extractor CLI Output

When using the extractor CLI, generated JSON is stored under:

```text
components/extractor/output/<document_name>/<document_name>.json
```

The repository already includes sample extracted JSON files under `components/extractor/output/`.

## Known Implementation Notes

- Docker Compose is the most reliable execution path for the current codebase.
- The backend database and upload folders are hard-coded under `/app/data`.
- The current extractor supports only document formats configured in `components/extractor/configs/`.
- The current included format is `Switch Invoice`.
- The frontend upload widget accepts only PDF files.
- The OCR API writes uploaded content to a temporary file with `.pdf` suffix before sending it to Veryfi.
- Authentication is basic: the backend returns user information after login, but it does not issue JWT tokens or protect project endpoints with authenticated sessions.
- Project endpoints use `user_id` query parameters for project creation and listing.
- Manual edits made in the frontend line-item table are not currently written back to the backend database.
- The `row_math` validator rule currently computes `quantity * rate = amount` directly, even though the JSON config also contains `expression` and `equals` fields.
- The parser appends multiline row overflow text to the first configured line-item column.

## Troubleshooting

### OCR service not initialized

Cause: Missing Veryfi credentials.

Check that `.env` exists in the project root and contains:

```env
VERYFI_CLIENT_ID=...
VERYFI_CLIENT_SECRET=...
VERYFI_USERNAME=...
VERYFI_API_KEY=...
```

Then restart the OCR service.

### Backend says required environment variables are missing

Cause: `OCR_URL`, `EXTRACTOR_URL`, or `VALIDATOR_URL` is not set.

With Docker Compose, these are already configured. For local execution, set them manually before starting the backend.

### Extractor returns “format not configured”

Cause: The OCR text did not match any `signature_regex` in `components/extractor/configs/`.

Recommended checks:

1. Inspect the OCR text returned by the OCR service.
2. Confirm that a matching config exists.
3. Test the `signature_regex` against the first page of OCR text.
4. Restart the extractor after adding or changing config files.

### Validation fails even when extraction looks correct

Possible causes:

- Numeric fields were extracted incorrectly.
- The document total does not equal the sum of extracted amounts within the configured tolerance.
- Header field `total_amount` was not extracted.
- OCR errors changed numbers or punctuation.

Check the downloadable validation log in the project result view.

### PDF does not display in the frontend

Possible causes:

- The backend could not retrieve the stored PDF.
- The PDF was deleted from `/app/data/uploads`.
- PyMuPDF failed to render the selected page.

Open backend logs and confirm that `/projects/{project_id}/pdf` returns the file correctly.

### Port already in use

Default ports:

```text
Frontend: 8501
Backend: 8000
OCR: 8001
Extractor: 8002
Validator: 8003
```

Stop the conflicting process or change the ports in `docker-compose.yml` and the related environment variables.

## Suggested Development Workflow

1. Run the full application with Docker Compose.
2. Test the target document in the UI.
3. If extraction fails, call the OCR service directly and inspect `ocr_text`.
4. Adjust or add extractor configs under `components/extractor/configs/`.
5. Test the extractor service directly with the OCR text.
6. Add matching validation configs under `components/validator/configs/`.
7. Restart affected services.
8. Re-run the document through the frontend.

