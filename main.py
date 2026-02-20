import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment variables")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,          # Set False in production
    pool_pre_ping=True  # Prevent stale connections
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Lifespan event (recommended instead of on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connected successfully!")
        yield
    finally:
        await engine.dispose()
        print("🛑 Database connection closed")

app = FastAPI(lifespan=lifespan)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/")
async def root():
    return {"message": "Revenue Engine Running 🚀"}

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "OK"}
