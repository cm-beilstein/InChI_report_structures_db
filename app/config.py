from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic automatically reads from environment variables
    database_url: str 
    
    # Configure Pydantic to read from a .env file locally
    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()
