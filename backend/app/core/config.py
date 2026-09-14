from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")
    database_url: str = "sqlite:///./newsmind.db"
    demo_mode: bool = True
    newsapi_key: str = ""
    openai_api_key: str = ""
    ai_model: str = "gpt-5-mini"
    ai_provider: str = "none"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    ops_token: str = ""
    supabase_url: str = ""
    fetch_interval_seconds: int = 3600
    cleanup_interval_seconds: int = 300
    news_provider: str = "rss"
    rss_feeds: str = "ndtv-india|ndtv-world|ndtv-sports|gadgets360|hindu-tamilnadu|bbc-world|bbc-sports|bbc-technology|bbc-politics"
    news_queries: str = "Tamil Nadu OR Chennai|India|world diplomacy|sports cricket football|software artificial intelligence|technology product launch|politics elections policy"


settings = Settings()
