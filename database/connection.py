# database/connection.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # 
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = "sqlite:///career_agent.db"

# Engine: The starting point for SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal: The actual database session/connection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Define Base for ORM models
Base = declarative_base()
# engine = create_engine("sqlite:///career_agent.db", ...)
# SessionLocal = sessionmaker(...)

def get_db():
    """Dependency that provides a session for FastAPI/Streamlit."""
    db = SessionLocal()
    try:
        yield db
        
    finally:
        db.close()
