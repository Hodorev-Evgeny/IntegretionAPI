from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PGUSER: str
    PASSWORD: str
    HOST: str
    PGPORT: int
    PGDATABASE: str

    ONEC_UNF_URL: str
    ONEC_BP_URL: str
    ONEC_LOGIN: str | None = None
    ONEC_PASSWORD: str | None = None
    ONEC_TIMEOUT: int = 30
    ONEC_MOCK: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.PGUSER}:{self.PASSWORD}"
            f"@{self.HOST}:{self.PGPORT}"
            f"/{self.PGDATABASE}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()