import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "AI Agent Web Generator"
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-2025-08-07")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    allowed_hosts: list = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # Database (for future use)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ai_agent.db")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Generation settings
    max_generation_time: int = int(os.getenv("MAX_GENERATION_TIME", "300"))  # 5 minutes
    max_files_per_generation: int = int(os.getenv("MAX_FILES_PER_GENERATION", "50"))
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "102400"))  # 100KB
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_default_model() -> str:
    """Get the default AI model"""
    settings = get_settings()
    return settings.openai_model

def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    settings = get_settings()
    return settings.debug

def get_api_url() -> str:
    """Get the API base URL"""
    settings = get_settings()
    return settings.api_base_url

def get_openai_config() -> dict:
    """Get OpenAI configuration"""
    settings = get_settings()
    return {
        "api_key": settings.openai_api_key,
        "model": settings.openai_model
    }

def validate_environment() -> dict:
    """Validate the environment configuration"""
    settings = get_settings()
    issues = []
    
    # Check required environment variables
    if not settings.openai_api_key:
        issues.append("OPENAI_API_KEY is not set")
    
    if not settings.secret_key or settings.secret_key == "your-secret-key-change-in-production":
        issues.append("SECRET_KEY should be changed in production")
    
    # Check API configuration
    if settings.api_port < 1 or settings.api_port > 65535:
        issues.append("API_PORT must be between 1 and 65535")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "environment": settings.environment,
        "debug": settings.debug
    } 