from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import admin, automations, instagram, queue, users
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.db.seed import seed_defaults
import app.models  # noqa: F401  (register all tables on Base.metadata)

# Columns added after the initial create_all (which never ALTERs existing
# tables). Each statement must be safe to re-run on every startup.
SCHEMA_PATCHES = [
    "ALTER TABLE queue_items ADD COLUMN IF NOT EXISTS thumbnail_path VARCHAR",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for statement in SCHEMA_PATCHES:
            await conn.execute(text(statement))
    async with AsyncSessionLocal() as db:
        await seed_defaults(db)
    yield


app = FastAPI(title="Logo Promotion Automation SaaS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api")
app.include_router(automations.router, prefix="/api")
app.include_router(queue.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(instagram.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
