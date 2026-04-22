# Deployment Notes

- Designed for local deployment with SQLite (`data/assistant.db`).
- For production, place FastAPI behind HTTPS reverse proxy (Nginx/Caddy).
- Set environment variables through secret manager or host environment.
- Disable `reload=True` in `scripts/run_backend.py` for production.

