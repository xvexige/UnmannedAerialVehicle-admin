from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "无人机SaaS平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库
    DATABASE_URL: str = "mysql+aiomysql://root:123456@localhost:3306/drone_saas"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-very-long-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 120
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_VIDEO: str = "drone-videos"
    MINIO_BUCKET_MODELS: str = "ai-models"
    MINIO_BUCKET_SCREENSHOTS: str = "drone-screenshots"
    MINIO_SECURE: bool = False

    # AI推理服务
    INFERENCE_SERVICE_URL: str = "http://localhost:8001"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:4200", "http://127.0.0.1:4200"]

    # 连接池
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
