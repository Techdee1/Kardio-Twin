import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

Base = declarative_base()

def _create_engine(url: str):
    """Create engine with appropriate settings for the database type."""
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    else:
        return create_engine(url, pool_pre_ping=True, pool_recycle=300)

def _get_database_url() -> tuple[str, any]:
    """Get database URL and create engine, with fallback to SQLite if connection fails."""
    # Try DATABASE_URL first
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        SUPABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
        if SUPABASE_PASSWORD:
            DATABASE_URL = f"postgresql://postgres:{SUPABASE_PASSWORD}@db.cgmlwqgnaqszhqljzbid.supabase.co:5432/postgres"
    
    # If we have a PostgreSQL URL, test the connection
    if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
        try:
            test_engine = _create_engine(DATABASE_URL)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Connected to PostgreSQL database")
            return DATABASE_URL, test_engine
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            print("Falling back to SQLite database")
    
    # Fallback to SQLite
    sqlite_url = "sqlite:///./cardiotwin.db"
    print("Using SQLite database")
    return sqlite_url, _create_engine(sqlite_url)

# Initialize database connection
_db_url, engine = _get_database_url()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()