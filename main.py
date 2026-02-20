import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load .env for local dev only (Render ignores this safely)
load_dotenv()

# -------------------------------------------------------------------
# DATABASE CONFIG — FIXED FOR RENDER (Feb 2026)
# -------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "❌ DATABASE_URL is not set!\n"
        "Go to Render Dashboard → Your Service → Environment → "
        "Click 'Add Database' and link your Postgres instance."
    )

# 🔥 AUTO-FIX: Render now gives "postgresql://" 
# We need "postgresql+asyncpg://" for asyncpg driver
print(f"🔧 Original DATABASE_URL scheme: {DATABASE_URL.split('://')[0] if '://' in DATABASE_URL else 'NONE'}")

if "+asyncpg" not in DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

print(f"✅ Final DATABASE_URL scheme: {DATABASE_URL.split('://')[0]}")

# Safety check
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise RuntimeError(f"❌ Still invalid DATABASE_URL: {DATABASE_URL}")

# -------------------------------------------------------------------
# ASYNC ENGINE
# -------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,                     # Keep False in production
    pool_pre_ping=True,             # Prevents stale connections on Render
    connect_args={"statement_cache_size": 0},  # Fixes asyncpg issues
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# -------------------------------------------------------------------
# APP LIFESPAN
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connected successfully")
        yield
    finally:
        await engine.dispose()
        print("🛑 Database connection closed")

# -------------------------------------------------------------------
# FASTAPI APP
# -------------------------------------------------------------------
app = FastAPI(
    title="Revenue Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# -------------------------------------------------------------------
# DEPENDENCIES
# -------------------------------------------------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# -------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Revenue Engine Running 🚀"}

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "OK", "database": "connected"}
