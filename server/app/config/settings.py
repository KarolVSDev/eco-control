from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://eco_user:eco_pass@localhost:5432/eco_control"
    jwt_secret: str = "dev-secret"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:4200"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def cors_list(self):
        return [x.strip() for x in self.cors_origins.split(',') if x.strip()]
settings = Settings()
