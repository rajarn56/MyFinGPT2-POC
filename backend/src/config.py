from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Authentication
    API_KEYS: str = "key1,key2,key3"
    SESSION_TIMEOUT_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

