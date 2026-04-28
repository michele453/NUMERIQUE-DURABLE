import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-key")
    DATABASE_URL = os.environ.get("DATABASE_URL", None)
    DATABASE = os.path.join(os.path.dirname(__file__), "..", "database", "evalconnect.db")
    PER_PAGE = 20