import os


# Ensure required settings can initialize during tests without real secrets.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LANGCHAIN_API_KEY", "test-key")
os.environ.setdefault("FREECURRENCY_API_KEY", "test-key")
os.environ.setdefault("FINNHUB_API_KEY", "test-key")
os.environ.setdefault("CHECKPOINT_DB_PATH", "./data/test-checkpoints.db")
