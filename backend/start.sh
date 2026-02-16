#!/bin/bash
set -e

echo "Running database migrations..."

# Convert async URL to sync for psql (postgresql+asyncpg:// → postgresql://)
SYNC_URL=$(echo "$DATABASE_URL" | sed 's|postgresql+asyncpg://|postgresql://|')

# Always run init.sql — all statements use IF NOT EXISTS / CREATE OR REPLACE
# so it's safe to re-run and will create any missing tables or functions.
python -c "
import asyncio, asyncpg, os

async def migrate():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    print('Applying init.sql (idempotent)...')
    with open('/app/migrations/init.sql', 'r') as f:
        await conn.execute(f.read())
    print('Migration complete.')
    await conn.close()

asyncio.run(migrate())
"

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
