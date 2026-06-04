# AgentDesk Backend

FastAPI backend skeleton for AgentDesk.

## Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
GET http://127.0.0.1:8000/api/v1/health
```
