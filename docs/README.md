# Multi-Function AI Assistant

## Quick Start

1. Create a virtual environment and install dependencies:
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

2. Initialize local configuration:
```bash
python scripts/setup.py
```

3. Set API keys in `.env`.

4. Run backend:
```bash
python scripts/run_backend.py
```

5. Run frontend:
```bash
python scripts/run_frontend.py
```

## Endpoints

- `POST /chat/stream`
- `GET /usage/stats?session_id=...`
- `GET /health`

