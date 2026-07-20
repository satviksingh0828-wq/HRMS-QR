"""
Configuration loader.

Priority:
1. config_baked.py — generated at build time by build.py, values hardcoded in.
   This is what gets compiled into the packaged .exe, so the exe needs no .env file.
2. .env file — used during development (`python main.py`), via python-dotenv.
"""
import os

try:
    from config_baked import (
        DEPT_CODE_URL,
        DEVICE_ID,
        DEVICE_PASSWORD,
        DEPARTMENT_LABEL,
        QR_CONTENT_TEMPLATE,
    )
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()

    def _require(name):
        val = os.environ.get(name)
        if not val:
            raise RuntimeError(
                f"Missing required environment variable: {name}. "
                f"Copy .env.example to .env and fill it in."
            )
        return val

    DEPT_CODE_URL = _require("DEPT_CODE_URL")
    DEVICE_ID = _require("DEVICE_ID")
    DEVICE_PASSWORD = _require("DEVICE_PASSWORD")
    DEPARTMENT_LABEL = os.environ.get("DEPARTMENT_LABEL", "")
    # {code}, {department}, {device_id} placeholders available
    QR_CONTENT_TEMPLATE = os.environ.get("QR_CONTENT_TEMPLATE", "{code}")
