"""Vercel Python serverless entrypoint for the TRINITY API.

Vercel invokes the exported ``handler`` for every request routed here by
``vercel.json``. Mangum translates between the ASGI application (FastAPI) and
the event/response shape the Vercel Python runtime speaks.

This file lives at ``backend/api/index.py`` so that, with the Vercel project's
Root Directory set to ``backend``, the surrounding ``app`` package is on disk
right next to it.
"""
import os
import sys

# Make the backend project root (the parent of this file's directory) importable
# so ``app`` resolves to the package beside it, whatever the runtime's cwd is.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mangum import Mangum  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

# lifespan="off": the app registers no startup/shutdown handlers, and Vercel
# owns the process lifetime per invocation. Exporting only ``handler`` keeps the
# entrypoint unambiguous for the runtime.
handler = Mangum(fastapi_app, lifespan="off")
