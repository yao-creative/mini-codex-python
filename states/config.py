from pydantic import BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = ".env"
