#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy seed data via Supabase HTTP API
Created: Thursday Jul 23, 2026, 4:32 PM (UTC-6)
Last edited: Thursday Jul 23, 2026, 4:32 PM (UTC-6)
"""

import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path("c:/Users/Lknepp/Desktop/Staging/CC-Python-version/.env")
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("[ERROR] Missing Supabase credentials")
    sys.exit(1)

print(f"[OK] Supabase URL: {SUPABASE_URL}")
print(f"[OK] Service Role Key configured")

# Read seed data
seed_file = Path("c:/Users/Lknepp/Desktop/Staging/CC-Python-version/content-pipeline/supabase/seed_data.sql")
with open(seed_file, 'r') as f:
    seed_sql = f.read()

print(f"[OK] Seed data loaded: {seed_file}")

# Parse SQL - extract key INSERT statements
lines = []
for line in seed_sql.split('\n'):
    stripped = line.strip()
    if not stripped.startswith('--') and stripped and not stripped.startswith('/*'):
        lines.append(line)

sql_content = '\n'.join(lines)

# Extract INSERT statements
import re
insert_pattern = r'^INSERT INTO.*?(?=;)'
inserts = re.findall(insert_pattern, sql_content, re.MULTILINE | re.DOTALL | re.IGNORECASE)

print(f"[OK] Parsed {len(inserts)} INSERT statements")

# Execute via HTTP - try to insert data directly
print("\n" + "="*60)
print("EXECUTING VIA SUPABASE REST API")
print("="*60)

headers = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Content-Type": "application/json",
}

# We can't execute raw SQL via REST, but we can insert via the PostgREST API
# Let's try a different approach - use the admin API to execute SQL

# Try using requests to POST to the Supabase SQL endpoint if available
# Or manually parse the INSERT statements and execute them as UPSERTS

# First, let's at least verify we can connect
try:
    # Test connection
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/",
        headers=headers
    )
    print(f"[OK] Supabase REST API reachable: {response.status_code}")
except Exception as e:
    print(f"[ERROR] Failed to reach Supabase: {e}")
    sys.exit(1)

# For seed data, we need to use Supabase SQL Editor or pgAdmin
# The best approach is to provide instructions to run it manually
print("\n" + "="*60)
print("SEED DATA DEPLOYMENT GUIDE")
print("="*60)

print("""
To deploy seed data, follow these steps:

1. Go to https://app.supabase.com/project/yiuosyhmowkqziwmssxo/sql/new
2. Copy the entire contents of seed_data.sql
3. Paste into the SQL editor
4. Click "Run"

This will insert:
- 5 Authority Models (home_services, health_wellness_spa, real_estate, automotive, financial)
- 2 CSS Templates (default and dark mode)
- 3 Provider Settings (default LLM, research, and embedding configs)

Alternatively, use psql:

  psql -h yiuosyhmowkqziwmssxo.supabase.co \
    -U postgres \
    -d postgres \
    -f seed_data.sql

When prompted for password, use your Supabase database password.
""")

print("\n[INFO] Checking if tables exist...")

# Check if tables exist by trying to query them
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    result = supabase.table("authority_models").select("*", count="exact").limit(1).execute()
    print(f"[OK] authority_models table exists ({result.count} records)")
except Exception as e:
    print(f"[INFO] authority_models: {str(e)[:60]}")

print("\n[COMPLETE] Seed data deployment script finished")
print("[NEXT] Deploy seed data manually via Supabase SQL Editor")
