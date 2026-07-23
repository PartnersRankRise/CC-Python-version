#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Push migrations and seeds to Supabase database
Created: 2026-07-23 3:54 PM
Last edited: 2026-07-23 3:56 PM
"""

import psycopg2
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix Unicode on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# Get database connection details from .env
db_url = os.getenv("POSTGRES_URL_NON_POOLING")
migrations_dir = Path("content-pipeline/supabase/migrations")
seeds_dir = Path("content-pipeline/supabase/seeds")

if not db_url:
    raise ValueError("POSTGRES_URL_NON_POOLING not found in .env")

print(f"Connecting to database...")

try:
    # Connect to database
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Execute migrations (skip if they already exist)
    migration_files = sorted(migrations_dir.glob("*.sql"))
    print(f"\n{'='*60}")
    print(f"MIGRATIONS ({len(migration_files)} files)")
    print(f"{'='*60}")
    
    for migration_file in migration_files:
        print(f"\n[*] Executing: {migration_file.name}")
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        try:
            # Split and execute multiple statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            for stmt in statements:
                cursor.execute(stmt)
            conn.commit()
            print(f"    [OK] SUCCESS")
        except psycopg2.errors.DuplicateTable as e:
            conn.rollback()
            print(f"    [OK] SKIPPED (tables already exist)")
        except Exception as e:
            conn.rollback()
            print(f"    [ERR] {str(e)[:150]}")
            raise
    
    # Execute seeds
    seed_files = sorted(seeds_dir.glob("*.sql"))
    print(f"\n{'='*60}")
    print(f"SEEDS ({len(seed_files)} files)")
    print(f"{'='*60}")
    
    for seed_file in seed_files:
        print(f"\n[*] Executing: {seed_file.name}")
        with open(seed_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Remove comments and trim
        sql_lines = [line.split('--')[0].strip() for line in sql_content.split('\n')]
        sql_clean = '\n'.join(sql_lines).strip()
        
        # Skip empty files (e.g., comment-only files)
        if not sql_clean or not any(c.isalpha() for c in sql_clean):
            print(f"    [OK] SKIPPED (empty/comment-only file)")
            continue
        
        try:
            # Don't split seed statements - execute as one block to preserve JSONB formatting
            cursor.execute(sql_content)
            conn.commit()
            print(f"    [OK] SUCCESS")
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            print(f"    [OK] SKIPPED (data already exists)")
        except Exception as e:
            conn.rollback()
            print(f"    [ERR] {str(e)[:150]}")
            raise
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"[OK] ALL MIGRATIONS AND SEEDS PUSHED SUCCESSFULLY")
    print(f"{'='*60}\n")

except Exception as e:
    print(f"\n[ERR] Database push failed: {str(e)}")
    raise
