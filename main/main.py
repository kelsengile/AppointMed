"""Entry point that starts the AppointMed backend.

Run from the `main` folder:  python main.py
"""
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def run() -> None:
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    uvicorn.run("backend.backend:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run()