import os
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

# Create session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connected successfully!")
    except Exception as e:
        print("❌ Database connection failed:", e)
        raise e

@app.get("/")
async def root():
    return {"message": "Revenue Engine Running 🚀"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}
