import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Configuration
    API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Model name
    MODEL_NAME = "gemini-2.5-flash"
    
    # Hotel Configuration
    HOTEL_NAME = os.getenv("HOTEL_NAME", "LevLano Hotel")
    
    EXTRA_GUEST_FEE = 25  # per night
    BASE_GUEST_COUNT = 2  # guests included in base price
    
    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Telegram Bot token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/hotel_ai"
    )

    # Manager's Telegram user ID
    STAFF_TELEGRAM_ID = os.getenv("STAFF_TELEGRAM_ID")  
    
    @classmethod
    def validate(cls):
        if not cls.API_KEY:
            raise ValueError("API_KEY not set in environment variables")
        return True

settings = Settings()