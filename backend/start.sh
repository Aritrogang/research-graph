#!/bin/bash
set -e

echo "Running database migrations..."

# Convert async URL to sync for psql (postgresql+asyncpg:// → postgresql://)
SYNC_URL=$(echo "$DATABASE_URL" | sed 's|postgresql+asyncpg://|postgresql://|')

# Run init.sql if the papers table doesn't exist yet
python -c "
import asyncio, asyncpg, os

async def migrate():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    exists = await conn.fetchval(
        \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'papers')\"
    )
    if not exists:
        print('Applying init.sql...')
        with open('/app/migrations/init.sql', 'r') as f:
            await conn.execute(f.read())
        print('Migration complete.')
    else:
        print('Tables already exist, skipping migration.')
    await conn.close()

asyncio.run(migrate())
"

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
