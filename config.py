from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "Universal Web Scraper"
    app_version: str = "1.0.0"
    
    # API
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Worker
    worker_concurrency: int = 10
    worker_browser_instances: int = 5
    worker_timeout: int = 30
    
    # Playwright
    playwright_browser_type: str = "chromium"
    playwright_headless: bool = True
    playwright_timeout: int = 30000
    
    # Stealth
    stealth_user_agent_rotation: bool = True
    stealth_proxy_rotation: bool = False
    
    # Extraction
    extraction_provider: str = "openai"
    extraction_model: str = "gpt-4o-mini"
    extraction_temperature: float = 0.0
    extraction_max_tokens: int = 4000
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # Proxies
    proxies: List[str] = Field(default_factory=list)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
