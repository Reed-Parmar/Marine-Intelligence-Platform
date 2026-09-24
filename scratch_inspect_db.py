import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.app.db.database import execute_query

try:
    print("--- Inspecting auth.users ---")
    users = execute_query("SELECT id, email, role, aud, created_at, email_confirmed_at FROM auth.users ORDER BY created_at DESC LIMIT 20;")
    for u in users:
        print(f"User: id={u['id']}, email={u['email']}, role={u['role']}, confirmed={u['email_confirmed_at']}")

    print("\n--- Inspecting public.profiles ---")
    profiles = execute_query("SELECT id, email, full_name, role, institution, department, designation, created_at FROM public.profiles ORDER BY created_at DESC LIMIT 20;")
    for p in profiles:
        print(f"Profile: id={p['id']}, email={p['email']}, full_name={p['full_name']}, role={p['role']}")

    print("\n--- Specific Check for reed@gmail.com ---")
    reed_auth = execute_query("SELECT id, email, role, created_at FROM auth.users WHERE LOWER(email) = 'reed@gmail.com';")
    print(f"auth.users reed@gmail.com: {reed_auth}")

    reed_profile = execute_query("SELECT id, email, full_name, role FROM public.profiles WHERE LOWER(email) = 'reed@gmail.com';")
    print(f"public.profiles reed@gmail.com: {reed_profile}")

except Exception as e:
    print(f"DB inspection error: {e}", file=sys.stderr)
