"""
Development server entrypoint with scoped Uvicorn reload watching.
"""

import os

import uvicorn


if __name__ == "__main__":
    os.environ.setdefault("DEBUG", "false")

    uvicorn.run(
        "backend.app.main:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
        reload_dirs=[
            "backend/app",
            "data_pipeline/fusion",
            "data_pipeline/ingestion",
            "data_pipeline/quality_standardisation",
            "data_pipeline/shared",
            "data_pipeline/specialized_science",
            "data_pipeline/storage",
        ],
        reload_excludes=[
            ".git/*",
            ".pytest_cache/*",
            ".venv/*",
            "analysis/*",
            "dataset/*",
            "docs/*",
            "frontend/*",
            "ml/*",
            "rag/*",
            "pytest-cache-files-*/*",
            "scratch_*.py",
            "*.csv",
            "*.txt",
            "*.xlsx",
            "*.parquet",
        ],
    )
