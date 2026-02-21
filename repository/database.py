import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Use full DATABASE_URL from env, or construct from password, or fallback to SQLite
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    SUPABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
    if SUPABASE_PASSWORD:
        DATABASE_URL = f"postgresql://postgres:{SUPABASE_PASSWORD}@db.cgmlwqgnaqszhqljzbid.supabase.co:5432/postgres"
    else:
        # Fallback to SQLite for local development
        DATABASE_URL = "sqlite:///./cardiotwin.db"
        print("Using SQLite database for local development")

# SQLite needs special connect_args
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()