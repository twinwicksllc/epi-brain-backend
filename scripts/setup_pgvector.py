#!/usr/bin/env python3
import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.config import settings


def check_pgvector():
    print("=" * 60)
    print("pgvector Extension Setup")
    print("=" * 60)
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print()
    
    db_url_lower = settings.DATABASE_URL.lower()
    if 'sqlite' in db_url_lower:
        print("You are using SQLite")
        print()
        print("pgvector requires PostgreSQL.")
        print()
        print("Options:")
        print("1. Use PostgreSQL with Docker")
        print("2. Test on Render.com (production)")
        print()
        return False
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            print(f"PostgreSQL: {result.fetchone()[0][:50]}...")
            print()
            
            result = conn.execute(text("SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = 'vector'"))
            extension_info = result.fetchone()
            
            if not extension_info:
                print("pgvector is NOT installed")
                print("Enable it on Render: Dashboard > Extensions > pgvector")
                return False
            
            name, default_version, installed_version = extension_info
            print(f"pgvector available: {name}")
            print(f"Installed: {installed_version or 'No'}")
            print()
            
            if not installed_version:
                print("Installing pgvector...")
                conn.execute(text("CREATE EXTENSION vector"))
                conn.commit()
                print("Installed successfully!")
            else:
                print("Already installed and enabled")
            
            conn.execute(text("CREATE TABLE IF NOT EXISTS pgvector_test (id SERIAL PRIMARY KEY, embedding vector(1536))"))
            conn.commit()
            conn.execute(text("DROP TABLE IF EXISTS pgvector_test"))
            conn.commit()
            print("Test passed!")
            print()
            print("pgvector setup complete!")
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    if check_pgvector():
        print("Ready to build semantic memory!")
    else:
        print("Setup incomplete")
        sys.exit(1)
