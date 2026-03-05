import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Read connection parameters from .env
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "message2")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "message2")
POSTGRES_DB = os.getenv("POSTGRES_DB", "message2")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Synchronous engine (for creating tables and migrations)
engine = create_engine(DATABASE_URL)

# Session for working with a database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Function for getting a session (will use it in FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
