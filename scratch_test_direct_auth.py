import json
from backend.app.db.database import execute_write, execute_single

try:
    user_metadata = json.dumps({
        "full_name": "Dr. Shreya Menon",
        "institution": "CMLRE Kochi",
        "department": "Molecular Marine Biology",
        "designation": "Senior Scientist",
        "role": "user"
    })
    res = execute_write("""
        INSERT INTO auth.users (
            id, email, encrypted_password, email_confirmed_at,
            raw_app_meta_data, raw_user_meta_data, created_at, updated_at, role, aud
        )
        VALUES (
            gen_random_uuid(),
            'test_scientist_direct@cmlre.gov.in',
            extensions.crypt('CmlreSecurePassword2026!', extensions.gen_salt('bf')),
            NOW(),
            '{"provider":"email","providers":["email"]}'::jsonb,
            CAST(:user_metadata AS jsonb),
            NOW(),
            NOW(),
            'authenticated',
            'authenticated'
        )
        RETURNING id, email;
    """, {"user_metadata": user_metadata})
    print("Direct user created in auth.users:", res)
    
    # Check if trigger created profile
    p = execute_single("SELECT * FROM public.profiles WHERE email = 'test_scientist_direct@cmlre.gov.in'")
    print("Trigger created profile:", p)
except Exception as e:
    print("Error:", e)
