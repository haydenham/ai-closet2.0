#!/usr/bin/env python3
"""
Debug script to check actual closet contents and categories
"""
import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.append('/Users/haydenhamilton/AI-CLOSET-PRODUCTION/ai-closet2.0/backend')

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.models.clothing_item import ClothingItem
from app.core.config import settings

def debug_actual_closet():
    """Debug the actual closet contents in the database"""
    try:
        # Create database connection
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as db:
            # Get all clothing items
            result = db.execute(select(ClothingItem))
            items = result.scalars().all()
            
            print(f"=== ACTUAL CLOSET CONTENTS ===")
            print(f"Total items found: {len(items)}")
            
            if not items:
                print("No items found in closet!")
                return
                
            # Group by category
            categories = {}
            for item in items:
                category = item.category.lower()
                if category not in categories:
                    categories[category] = []
                categories[category].append(item)
            
            print(f"\nCategories found: {list(categories.keys())}")
            
            for category, items_in_category in categories.items():
                print(f"\n--- {category.upper()} ({len(items_in_category)} items) ---")
                for item in items_in_category:
                    print(f"  ID: {item.id}")
                    print(f"  Color: {item.color}")
                    print(f"  Brand: {item.brand}")
                    print(f"  Tags: {item.tags}")
                    print(f"  Description: {item.description}")
                    print()
    
    except Exception as e:
        print(f"Error accessing database: {e}")
        print("Make sure the database is running and accessible.")

if __name__ == "__main__":
    debug_actual_closet()
