from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Task Manager API"
    DATABASE_URL: str = "mysql+pymysql://root:123456@127.0.0.1:3306/task_manager?charset=utf8mb4"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()