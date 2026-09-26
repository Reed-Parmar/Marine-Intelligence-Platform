"""
Development server entrypoint with scoped Uvicorn reload watching.
"""

import os
import pathlib

import uvicorn

# Load .env from the project root before anything else so that
# DATABASE_URL and other secrets are available to all processes.
_project_root = pathlib.Path(__file__).resolve().parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=str(_env_file), override=False)
    except ImportError:
        # dotenv not installed – parse manually
        with open(_env_file, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())


if __name__ == "__main__":
    os.environ.setdefault("DEBUG", "false")

    uvicorn.run(
        "backend.app.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
        reload_dirs=[
            "backend/app",
            "ml",
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
            "rag/*",
            "pytest-cache-files-*/*",
            "scratch_*.py",
            "*.csv",
            "*.txt",
            "*.xlsx",
            "*.parquet",
        ],
    )
