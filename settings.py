import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TELE_API_ID: int = int(os.getenv("TELE_API_ID", 0))
    TELE_API_HASH: str = os.getenv("TELE_API_HASH", "")
    TELE_BOT_TOKEN: str = os.getenv("TELE_BOT_TOKEN", "")

    WFM_USERNAME: str = os.getenv("WFM_USERNAME", "")
    WFM_PASSWORD: str = os.getenv("WFM_PASSWORD", "")

settings = Settings()