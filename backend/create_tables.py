#!/usr/bin/env python3
"""
Simple script to create all database tables from SQLAlchemy models
This bypasses migrations for development setup
"""

import asyncio
from app.core.database import async_engine
from app.models import *  # Import all models
from sqlalchemy.ext.asyncio import AsyncConnection

async def create_tables():
    """Create all tables defined in SQLAlchemy models"""
    from app.models.base import Base
    
    async with async_engine.begin() as conn:
        # Drop all tables first (for clean slate)
        print("Dropping all existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        print("Creating all tables from models...")
        await conn.run_sync(Base.metadata.create_all)
        
        print("✅ All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
