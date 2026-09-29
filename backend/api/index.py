"""Vercel Python entrypoint for the TRINITY API.

Vercel's Python runtime serves an ASGI application exported as ``app``
directly. Mangum is an AWS-Lambda adapter and makes the function crash on
import when used as the Vercel entrypoint, so it is not used here.

This file sits at ``backend/api/index.py`` so that, with the Vercel project's
Root Directory set to ``backend``, the ``app`` package is right beside it.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.main import app  # noqa: E402,F401  (re-exported for Vercel)
