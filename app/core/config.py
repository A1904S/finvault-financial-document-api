from pydantic_settings import BaseSettings

# all the config settings are here
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/finvault"
    SECRET_KEY: str = "mysecretkey123"  # TODO change this later
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "financial_docs"
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"

settings = Settings()
