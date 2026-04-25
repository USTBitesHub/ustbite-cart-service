from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "ustbite-cart-service"
    service_port: int = 8010
    log_level: str = "INFO"

    # PostgreSQL connection string — injected from Kubernetes secret
    database_url: str = ""

    # JWT — must match the same secret used by user-service
    jwt_secret: str = "ustbite-jwt-secret-change-in-prod"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
