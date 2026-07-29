from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    app_name: str = "Eloquent Miner"
    app_env: str = "development"
    debug: bool = True

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "sqlite:///./data/db/app.db"
    media_dir: str = "./data/media"
    jobs_dir: str = "./data/jobs"

    ffmpeg_path: str = "ffmpeg"

    enable_transcript_upload: bool = True
    enable_subtitle_upload: bool = True
    enable_audio_upload: bool = True
    enable_video_upload: bool = False
    enable_youtube_url: bool = True
    enable_youtube_search: bool = False
    enable_youtube_download: bool = True

    # Generic LLM fallback
    llm_provider: str = "manual"
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""

    # OpenRouter specific
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_app_url: str = "http://localhost:8000"

    transcription_provider: str = "manual"

    # YouTube specific
    youtube_audio_format: str = "mp3"
    youtube_subtitle_langs: str = "en"


settings = Settings()