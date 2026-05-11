"""Configuration management for Naver Blog Automation"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# 프로젝트 루트 자동 계산 — 어디로 옮기든 동작
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings"""

    # Slack
    slack_bot_token: str
    slack_app_token: str
    slack_channel_id: str

    # Naver
    naver_id: str = "ridyservice"
    naver_pw: str
    naver_blog_url: str = "https://blog.naver.com/ridyservice"
    naver_blog_category: str = "출고 현황"  # Blog category for auto-posts

    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # Ollama (Backup)
    ollama_host: str = "http://192.168.75.44:11434"
    ollama_model: str = "llama3.2:latest"

    # Paths
    chrome_profile_path: str = str(BASE_DIR / "chrome_data")
    cookie_json_path: str = str(BASE_DIR / "naver_cookies.json")
    output_dir: str = "./output"
    
    # Footer URLs
    kakao_link_1: str = "https://pf.kakao.com/_xgxoxexen/chat"
    
    # Contact
    phone: str = "1555-6595"
    
    # Tags (from reference)
    default_tags: list[str] = [
        "#조종면허증", "#소형이륜", "#워커", "#이륜장비이사", "#취미보호정도",
        "#Xadv750", "#750cc", "#honda", "#운반도보거", "#라이디렌탈",
        "#리스", "#렌탈", "#라이디렌탈", "#중급렌탈이", "#림르보험"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global settings instance
settings = Settings()
