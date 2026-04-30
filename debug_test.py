"""Debug script to test the API"""
import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, Incident

# Create test database - use a file-based database instead of in-memory
test_engine = create_engine(
    "sqlite:///./test_debug.db",
    connect_args={"check_same_thread": False}
)

# Create tables
Base.metadata.create_all(bind=test_engine)

# Verify tables exist
from sqlalchemy import inspect
inspector = inspect(test_engine)
print(f"Tables: {inspector.get_table_names()}")

TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

response = client.post("/incidents/analyze", json={"log_text": "test"})
print(f"Status: {response.status_code}")
print(f"Body: {response.text}")