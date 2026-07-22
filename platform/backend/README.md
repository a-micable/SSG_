# Platform Backend (MVP)

FastAPI service that provides analysis APIs for the company-level code-quality platform.

Run locally for development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
