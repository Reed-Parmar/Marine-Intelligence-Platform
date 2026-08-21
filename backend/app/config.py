import os
from typing import List, Union
from pydantic import field_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings
    def SettingsConfigDict(**kwargs):
        return {"extra": "ignore"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load environment variables into attributes if not already set
        for k in self.__class__.model_fields.keys():
            if k in os.environ:
                val = os.environ[k]
                if isinstance(getattr(self, k), bool):
                    setattr(self, k, val.lower() in ("true", "1", "t"))
                elif isinstance(getattr(self, k), int):
                    try:
                        setattr(self, k, int(val))
                    except ValueError:
                        pass
                elif isinstance(getattr(self, k), str):
                    setattr(self, k, val)

    PROJECT_NAME: str = "CMLRE Marine Intelligence Platform API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database (Supabase PostgreSQL + PostGIS)
    DATABASE_URL: str = ""
    
    # Supabase Auth & Storage
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
