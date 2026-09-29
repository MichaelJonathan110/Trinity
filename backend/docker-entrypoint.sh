#!/bin/sh
# Container entrypoint: wait for the database, apply migrations, then serve.
# Used by Render (and anything that runs the Dockerfile directly).
set -e

PORT="${PORT:-8000}"

if [ -n "${DATABASE_URL:-}" ]; then
  echo "[entrypoint] waiting for the database..."
  i=0
  until python -c "
import os, sys
from sqlalchemy import create_engine, text
url = os.environ['DATABASE_URL']
for bare in ('postgres://', 'postgresql://'):
    if url.startswith(bare):
        url = 'postgresql+psycopg://' + url[len(bare):]
        break
try:
    create_engine(url, pool_pre_ping=True).connect().execute(text('select 1'))
except Exception as e:
    print(e, file=sys.stderr); sys.exit(1)
" 2>/dev/null; do
    i=$((i + 1))
    if [ "$i" -ge 30 ]; then
      echo "[entrypoint] database not reachable after 30 tries; continuing anyway"
      break
    fi
    sleep 2
  done
fi

echo "[entrypoint] applying migrations..."
alembic upgrade head

echo "[entrypoint] starting uvicorn on port ${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
