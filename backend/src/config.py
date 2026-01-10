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
    CHROMA_DATA_PATH: str = "./data/chroma"  # Local ChromaDB data storage path
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Authentication
    API_KEYS: str = "key1,key2,key3"
    SESSION_TIMEOUT_HOURS: int = 24
    
    # LLM Configuration (for Phase 2+)
    LLM_PROVIDER: str = "lmstudio"  # Options: openai, anthropic, gemini, lmstudio, ollama
    LM_STUDIO_API_BASE: str = "http://localhost:1234/v1"
    LM_STUDIO_MODEL: str = "local-model"
    OPENAI_API_KEY: str = ""  # Required for OpenAI provider
    OPENAI_MODEL: str = "gpt-4"
    
    # Embedding Configuration (for Phase 4+)
    # Embeddings can use a different provider/model than LLM calls
    EMBEDDING_PROVIDER: str = ""  # If empty, uses LLM_PROVIDER. Options: openai, lmstudio, etc.
    EMBEDDING_MODEL: str = ""  # Embedding model name. For LMStudio, set to your embedding model name
    # Default embedding models by provider (used if EMBEDDING_MODEL not set)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"  # OpenAI default
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

