#!/usr/bin/env python3
"""
Clear relevance filter cache to apply stricter filtering
"""
import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

cache_db = Path("cache/langchain.db")
relevance_table = "article_relevance"

if cache_db.exists():
    conn = sqlite3.connect(cache_db)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (relevance_table,))
    if cursor.fetchone():
        # Count before
        cursor.execute(f"SELECT COUNT(*) FROM {relevance_table}")
        count_before = cursor.fetchone()[0]
        
        # Clear the table
        cursor.execute(f"DELETE FROM {relevance_table}")
        conn.commit()
        
        print(f"✅ Cleared {count_before} cached relevance decisions")
        print("   Stricter AI filter will now apply to all articles")
    else:
        print("ℹ️  No relevance cache found")
    
    conn.close()
else:
    print("ℹ️  No cache database found")

