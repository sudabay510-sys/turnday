"""Turnday quiz-to-plan app. Local: python app.py · Render: gunicorn app:app"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from brands import BRANDS  # noqa: E402
from quiz_engine import create_app  # noqa: E402

brand = dict(BRANDS["turnday"])
brand["root"] = str(ROOT)
app = create_app(brand)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", brand["port"]))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
