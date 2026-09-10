import json
import os
import sys
import uuid
from backend.app.config import settings
from backend.app.db.database import execute_write, execute_single

# Environment guard: Only run in development or test environments
if settings.ENVIRONMENT not in ("development", "test"):
    print("Skipping direct auth test: Not permitted in non-development environment.")
    sys.exit(0)

test_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
test_password = os.getenv("TEST_AUTH_PASSWORD", "TestPassword123!")

inserted_user_id = None
try:
    user_metadata = json.dumps({
        "full_name": "Synthetic Test Researcher",
        "institution": "Test Marine Institute",
        "department": "Synthetic Testing Division",
        "designation": "Test Scientist",
        "role": "user"
    })

    res = execute_write("""
        INSERT INTO auth.users (
            id, email, encrypted_password, email_confirmed_at,
            raw_app_meta_data, raw_user_meta_data, created_at, updated_at, role, aud
        )
        VALUES (
            gen_random_uuid(),
            :email,
            extensions.crypt(:password, extensions.gen_salt('bf')),
            NOW(),
            '{"provider":"email","providers":["email"]}'::jsonb,
            CAST(:user_metadata AS jsonb),
            NOW(),
            NOW(),
            'authenticated',
            'authenticated'
        )
        RETURNING id, email;
    """, {
        "email": test_email,
        "password": test_password,
        "user_metadata": user_metadata
    })

    if not res:
        raise RuntimeError("Failed to insert synthetic user into auth.users.")

    inserted_user_id = str(res["id"])
    print(f"Direct test user created in auth.users with ID: {inserted_user_id}")

    # Verify profile existence with specific fields
    p = execute_single(
        "SELECT id, email, role, institution FROM public.profiles WHERE id = :user_id",
        {"user_id": inserted_user_id}
    )
    if not p:
        # Check by email if trigger didn't copy the id identically
        p = execute_single(
            "SELECT id, email, role, institution FROM public.profiles WHERE email = :email",
            {"email": test_email}
        )

    if not p:
        raise AssertionError("Profile was not created for test user.")

    print(f"Verified profile created: id={p['id']}, email={p['email']}, role={p['role']}")
    print("Direct auth test passed successfully.")

except Exception as e:
    print(f"Direct auth test failed: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    # Cleanup inserted test user and profile
    if inserted_user_id:
        try:
            execute_write("DELETE FROM public.profiles WHERE id = :user_id;", {"user_id": inserted_user_id})
            execute_write("DELETE FROM auth.identities WHERE user_id = :user_id::uuid;", {"user_id": inserted_user_id})
            execute_write("DELETE FROM auth.users WHERE id = :user_id::uuid;", {"user_id": inserted_user_id})
            print(f"Cleaned up test user {inserted_user_id}.")
        except Exception as clean_err:
            print(f"Warning: Cleanup failed: {clean_err}", file=sys.stderr)

