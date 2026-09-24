# Supabase Storage & Authentication Integration Guide

This guide provides the exact integration specifications for connecting the **React/Vite Frontend** and **FastAPI Backend** to the CMLRE Marine Intelligence Platform's Supabase instance.

---

## 1. Environment Configuration

Both Frontend and Backend require connection parameters. Ensure your local `.env` contains:

```env
# Frontend & Backend Shared
SUPABASE_URL=<supabase-project-url>
SUPABASE_ANON_KEY=<supabase-publishable-key>

# Backend Only (FastAPI / Direct SQL)
DATABASE_URL=<backend-only-secret>
# SUPABASE_SERVICE_ROLE_KEY=<backend-only-secret> (Optional, for backend admin operations)
```

---

## 2. Authentication & Roles

### Architecture
- **Provider**: Supabase Auth (Email / Password).
- **User Linkage**: `auth.users(id)` automatically mirrors to `public.profiles(id)` via the `on_auth_user_created` trigger.
- **Roles**:
  - `user`: Standard researcher/user (default assigned upon signup).
  - `admin`: Platform administrator with full management access.
  - *(Legacy domain roles `researcher`, `scientist`, `fisheries_manager`, `decision_maker`, `viewer` are also valid enum values if needed).*

### Test Credentials (Created for Development)
| Role | Email | Password | User ID |
| :--- | :--- | :--- | :--- |
| **User** | `researcher@cmlre.gov.in` | `<test-password>` | `a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d` |
| **Admin** | `admin@cmlre.gov.in` | `<test-password>` | `b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e` |

---

## 3. Storage Bucket & Path Conventions

### Bucket Details
- **Bucket ID**: `marine-files`
- **Visibility**: `private` (Public access = `false`)
- **Size Limit**: 100 MB per file
- **Allowed MIME Types**: `text/csv`, `text/plain` (TXT), `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (XLSX), `application/json`, `application/pdf`, `image/jpeg`, `image/png`, `image/webp`, `image/tiff`, `application/octet-stream`.

### Standard Logical Path Conventions
All files in `marine-files` must follow this path pattern:
```text
datasets/{dataset_id}/{filename}       # Primary for datasets (CSV, TXT, Excel, JSON)
edna/{sample_id}/{filename}             # FASTA / FASTQ / Sequence files
otolith/{sample_id}/{filename}          # Otolith images (JPG, PNG, TIFF)
```

Example storage path:
`datasets/d1a2b3c4-0000-0000-0000-000000000001/cmlre_arabian_sea_ctd_sample.txt`

---

## 4. Storage Security & RLS Policies

Row-Level Security (RLS) is active on `storage.objects`:
1. **SELECT**: Any `authenticated` user can view / download files in `marine-files`.
2. **INSERT**: Any `authenticated` user can upload files into `marine-files`.
3. **UPDATE / DELETE**: Any `authenticated` user can update/delete their own files or platform admins can update/delete any file.
4. **ANON**: Blocked from all storage operations.

---

## 5. Database ↔ Storage Integration

When a file is uploaded, store its metadata and storage path in `public.datasets`:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Primary Key for dataset |
| `project_id` | `UUID` | Associated project ID |
| `data_source_id` | `UUID` | Associated data source ID |
| `name` | `TEXT` | Human-readable dataset name |
| `domain_type` | `dataset_domain` | Enum: `oceanography`, `fisheries`, `biodiversity`, `edna`, `otolith`, etc. |
| `storage_file_path` | `TEXT` | Path in `marine-files` (e.g. `datasets/{id}/data.txt`) |
| `file_type` | `TEXT` | Extension (e.g., `'txt'`, `'csv'`, `'xlsx'`) |
| `file_size_bytes` | `BIGINT` | Size in bytes |
| `uploaded_by` | `UUID` | User ID (`auth.users.id`) |
| `status` | `processing_status` | Enum: `uploaded`, `processing`, `standardized`, `qc_passed`, `failed` |
| `quality_status` | `quality_flag` | Enum: `pending`, `passed`, `flagged`, `failed` |
| `quality_score` | `NUMERIC` | Quality score (e.g., `98.50`) |
| `validation_notes` | `TEXT` | Notes on QC/validation checks |
| `provenance_metadata`| `JSONB` | Ingestion metadata, source equipment, vessel info |

---

## 6. Frontend Integration (React / TypeScript)

```typescript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// 1. Sign In
export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data.session; // Contains access_token (JWT)
}

// 2. Upload file to Storage
export async function uploadDatasetFile(datasetId: string, file: File) {
  const filePath = `datasets/${datasetId}/${file.name}`;
  const { data, error } = await supabase.storage
    .from('marine-files')
    .upload(filePath, file, {
      cacheControl: '3600',
      upsert: true,
    });

  if (error) throw error;
  return filePath;
}

// 3. Download / Get Signed URL
export async function getFileUrl(filePath: string) {
  const { data, error } = await supabase.storage
    .from('marine-files')
    .createSignedUrl(filePath, 3600);

  if (error) throw error;
  return data.signedUrl;
}
```

---

## 7. Backend Integration (FastAPI / Python)

### Verifying JWT & Reading Dataset Metadata

> **Important Security Note**: The backend must **verify** the JWT signature using your Supabase project's JWT Secret. Simply decoding the payload without verification allows forged tokens.

```python
from fastapi import FastAPI, Depends, HTTPException, Header
import jwt
from sqlalchemy.orm import Session
# ...

# Ensure this secret is loaded securely from environment variables, NOT hardcoded.
SUPABASE_JWT_SECRET = "<backend-only-secret>" 

async def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    try:
        # Securely verify the JWT signature and audience
        payload = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"], 
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token signature")

@app.get("/api/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, current_user = Depends(get_current_user)):
    # Query datasets table from PostgreSQL
    # dataset.storage_file_path contains the reference in 'marine-files'
    return {"status": "success", "user": current_user["sub"]}
```
