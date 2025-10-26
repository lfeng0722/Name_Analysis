# 🧠 TV Title Normalisation Service

A production-ready **FastAPI** service that cleans and normalises messy TV program titles using rule-based regular expressions.

---

## 🚀 Overview

This project provides a simple API that takes “messy” broadcast titles (often containing session codes, day markers, replay flags, etc.) and returns a clean, canonical program title.  

It is designed as a **containerised microservice** with:
- ✅ REST API built with **FastAPI**
- ✅ Automated **unit and integration tests** (via `pytest`)
- ✅ Continuous Integration (CI) and Delivery (CD) via **GitHub Actions** (push to **GHCR**)
- ✅ Dockerised for reproducible deployment and testing
- ✅ Built-in **Prometheus** metrics at `/metrics`

---

## 📁 Project Structure

```
ml_title_normaliser/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entrypoint
│   └── model.py             # Core normalisation logic (regex-based)
│
├── tests/
│   ├── conftest.py
│   ├── pytest.ini
│   ├── unit/
│   │   └── test_model.py    # Unit tests for the normalisation function
│   └── integration/
│       └── test_api.py      # Integration tests for API endpoints
│
├── Dockerfile               # Production image
├── Dockerfile.test          # Image for containerised testing
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        ├── tests.yml        # Runner-based CI
        ├── tests-docker.yml # Dockerised CI
        └── cd.yml           # Build & publish image to GHCR
```

---

## 🧩 API Endpoints

### `POST /normalise`
Clean a single title.

**Request:**
```json
{"messy_title": "BILLY THE EXTERMINATOR-DAY (R)"}
```

**Response:**
```json
{"clean_title": "BILLY THE EXTERMINATOR"}
```

---

### `POST /normalise-batch`
Clean multiple titles in one request.

**Request:**
```json
{"messy_titles": ["GOTHAM -RPT", "HOT SEAT -5PM", "MIXOLOGY-EARLY(R)"]}
```

**Response:**
```json
{"clean_titles": ["GOTHAM", "HOT SEAT", "MIXOLOGY"]}
```

---

### `GET /metrics`
Prometheus exposition format for monitoring. Includes default Python/Process metrics and app-specific HTTP metrics:
- `http_requests_total{method, path, status}`
- `http_request_duration_seconds_{bucket,sum,count}{method, path, status}`

Quick check:
```bash
curl -s http://localhost:8000/metrics | grep -E 'http_requests_total|http_request_duration_seconds'
```

---

## 🧠 Core Logic

The cleaning logic in `app/model.py` applies multiple regular expressions to iteratively strip noise such as:

| Pattern Category | Examples Removed |
|------------------|------------------|
| Replay flags | `(R)`, `-RPT`, `ENCORE` |
| Time markers | `-5PM`, `-PM`, `-EARLY` |
| Weekday or day parts | `-MON`, `-DAY`, `-NIGHT` |
| Session info | `S01`, `E02`, `PART 2`, `FEED3`, `TX1` |
| Prefix markers | `M-` |
| Weather/delay tags | `RAIN DEL` |

The function runs **recursively** until no further patterns match, ensuring deep cleaning for stacked suffixes.

---

## 🧪 Testing

### 1️⃣ Unit Tests
- Located in `tests/unit/test_model.py`
- Validate `normalise_title()` with:
  - Simple cases
  - Unicode inputs
  - Recursive removals
  - Pure-noise strings (edge cases)

### 2️⃣ Integration Tests
- Located in `tests/integration/test_api.py`
- Validate both `/normalise` and `/normalise-batch` endpoints
- Include **edge cases** from real datasets:
  - Day/time markers (`-PM TX1`, `DAY 2 FEED2`)
  - Weekdays and day parts (`-THU`, `-EV`)
  - Season/day codes (`S1`, `D4 S2 RAIN DEL`)
  - Prefix and replay flags (`M-`, `(R)`)
  - Empty or noise-only inputs

### Run tests locally:
```bash
# run all tests
pytest

# or run specific groups
pytest -m unit
pytest -m integration
```

### Test Coverage (optional)
```bash
pip install coverage
coverage run -m pytest
coverage report -m
```

---

## 🐳 Docker Setup

### Build and run service
```bash
docker build -t title-normaliser .
docker run -p 8000:8000 title-normaliser
```

Access the interactive docs:  
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

Check metrics quickly:  
👉 `http://localhost:8000/metrics`

### Build and run tests inside Docker
```bash
docker build -f Dockerfile.test -t normaliser-tests .
docker run --rm normaliser-tests pytest -q
```

---

## ⚙️ Continuous Integration (CI)

This repository includes **two automated CI pipelines**:

### 1️⃣ `.github/workflows/tests.yml`
Runs on GitHub’s hosted Ubuntu runner:
- Installs dependencies
- Runs **unit + integration tests**
- Generates and uploads `coverage.xml`

### 2️⃣ `.github/workflows/tests-docker.yml`
Runs in a **Dockerised environment**:
- Builds the test image (`Dockerfile.test`)
- Runs tests inside the container
- Builds the production image
- Performs black-box checks using `curl`:
  - `/openapi.json` reachable
  - `/normalise` and `/normalise-batch` return expected results

Both workflows trigger automatically on:
- Push or PR to `main`
- Manual run (`workflow_dispatch`)

---

## 🚢 Continuous Delivery (CD) to GHCR

`cd.yml` builds and publishes the production image to **GitHub Container Registry (GHCR)**:
- Triggers on push to `main` and tags matching `v*` (e.g., `v1.0.0`).
- Image reference: `ghcr.io/<owner>/<repo>:<tag>`

Pull and run:
```bash
docker pull ghcr.io/<owner>/<repo>:latest
docker run -p 8000:8000 ghcr.io/<owner>/<repo>:latest
```

Notes:
- For private packages, login with a PAT that has `read:packages`.
- Use semantic tags (`vX.Y.Z`) for immutable releases, or pin by digest.

---

## 🔍 CI Verification Steps

1. Push your branch to GitHub:
   ```bash
   git add .
   git commit -m "Add CI and tests"
   git push origin feat/ci-tests
   ```

2. Create a PR → `main`  
   GitHub Actions will automatically:
   - Run all tests  
   - Show status checks in PR  
   - Upload coverage artifacts

3. Merge after all checks pass ✅

---

## 📈 Observability & Monitoring

### Prometheus scrape example
```yaml
scrape_configs:
  - job_name: normaliser
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:8000']
```

### Common Grafana panels (PromQL)
- QPS: `sum by (path,status) (rate(http_requests_total[1m]))`
- P95: `histogram_quantile(0.95, sum by (le,path) (rate(http_request_duration_seconds_bucket[5m])))`

---

## 📈 Future Improvements
- Add versioned model rules (e.g. via config file or S3)
- Add request/response logging (e.g. `loguru`)
- Error rate metrics and tracing
- Optional async batch processing
- Deploy to AWS ECS or GCP Cloud Run


