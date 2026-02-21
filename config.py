import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cardiotwin.db")
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "https://cardiotwinai-service.azurewebsites.net")
    CALIBRATION_THRESHOLD: int = int(os.getenv("CALIBRATION_THRESHOLD", "15"))

settings = Settings()
