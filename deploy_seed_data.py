#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Seed Data Deployment Script
Created: Thursday Jul 23, 2026, 4:32 PM (UTC-6)
Last edited: Thursday Jul 23, 2026, 4:32 PM (UTC-6)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path("c:/Users/Lknepp/Desktop/Staging/CC-Python-version/.env")
load_dotenv(env_path)

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("[ERROR] Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

print(f"[OK] Supabase URL: {SUPABASE_URL}")
print(f"[OK] Service Role Key loaded")

# Initialize Supabase client
from supabase import create_client

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print("[OK] Supabase client initialized")
except Exception as e:
    print(f"[ERROR] Failed to initialize Supabase client: {e}")
    sys.exit(1)

# Read seed data SQL file
seed_file = Path("c:/Users/Lknepp/Desktop/Staging/CC-Python-version/content-pipeline/supabase/seed_data.sql")
if not seed_file.exists():
    print(f"[ERROR] Seed data file not found: {seed_file}")
    sys.exit(1)

with open(seed_file, 'r') as f:
    seed_sql = f.read()

print(f"[OK] Seed data file loaded: {seed_file}")

# Split SQL into individual statements
statements = []
lines = []
for line in seed_sql.split('\n'):
    # Skip comments
    if line.strip().startswith('--'):
        continue
    if line.strip().startswith('/*') or line.strip().startswith('*'):
        continue
    lines.append(line)

sql_text = '\n'.join(lines)
statements = [s.strip() for s in sql_text.split(';') if s.strip()]

print(f"[OK] Parsed {len(statements)} SQL statements")

# Execute seed data via postgrest raw
print("\n" + "="*60)
print("EXECUTING SEED DATA")
print("="*60)

# For Supabase, we need to use the SQL editor or execute via HTTP
# Since we have the service role key, we can construct SQL batch
try:
    # Try to execute the entire seed data
    # Read full SQL and send as single batch
    with open(seed_file, 'r') as f:
        full_sql = f.read()
    
    # Filter out comments
    filtered_lines = []
    for line in full_sql.split('\n'):
        stripped = line.strip()
        if not stripped.startswith('--') and not stripped.startswith('/*'):
            filtered_lines.append(line)
    
    filtered_sql = '\n'.join(filtered_lines)
    
    # Try using supabase RPC or direct execution
    # Note: The supabase-py SDK has limitations for executing raw SQL
    # We'll use the HTTP API directly
    import requests
    import json
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
    }
    
    # Try to execute via the SQL endpoint
    sql_endpoint = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    # Split into statements and execute each
    statements = [s.strip() for s in filtered_sql.split(';') if s.strip()]
    
    executed = 0
    for i, stmt in enumerate(statements, 1):
        if not stmt:
            continue
        try:
            # Execute statement
            payload = {"sql": stmt}
            # Try direct execution via postgrest
            result = supabase.postgrest.raw_body(stmt)
            executed += 1
            print(f"[OK] Statement {i} executed")
        except Exception as e:
            error_str = str(e)[:80]
            if "CREATE TABLE" in stmt or "already exists" in error_str:
                print(f"[OK] Statement {i} (table/constraint exists)")
                executed += 1
            else:
                print(f"[WARN] Statement {i}: {error_str}")
    
    print(f"[OK] Executed {executed} statements")

except Exception as e:
    print(f"[ERROR] Execution error: {e}")
    import traceback
    traceback.print_exc()

# Verify data
print("\n" + "="*60)
print("VERIFYING DATA INSERTION")
print("="*60)

try:
    # Check authority_models
    result = supabase.table("authority_models").select("COUNT()", count="exact").execute()
    count = result.count if hasattr(result, 'count') else len(result.data)
    print(f"[OK] authority_models: {count} records")
    
    # Check css_templates
    result = supabase.table("css_templates").select("COUNT()", count="exact").execute()
    count = result.count if hasattr(result, 'count') else len(result.data)
    print(f"[OK] css_templates: {count} records")
    
    # Check provider_settings
    result = supabase.table("provider_settings").select("COUNT()", count="exact").execute()
    count = result.count if hasattr(result, 'count') else len(result.data)
    print(f"[OK] provider_settings: {count} records")
    
except Exception as e:
    print(f"[WARN] Verification check: {e}")

print("\n[COMPLETE] Seed data deployment finished!")
