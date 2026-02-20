import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load .env for local dev (Render ignores this safely)
load_dotenv()

# -------------------------------------------------------------------
# DATABASE CONFIG
# -------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL is not set")

# 🔥 REQUIRED FIX FOR RENDER + SQLALCHEMY ASYNC
# Render gives: postgres://
# SQLAlchemy async needs: postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+asyncpg://",
        1,
    )

# -------------------------------------------------------------------
# ASYNC ENGINE
# -------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,                 # ❗ keep False in production
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0  # Prevent asyncpg cache issues on Render
    },
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# -------------------------------------------------------------------
# APP LIFESPAN (startup / shutdown)
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
    return {"status": "OK"}
