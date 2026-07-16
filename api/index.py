import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app  # noqa: E402,F401  (Vercel Python 런타임이 이 `app`을 ASGI 핸들러로 사용)
