import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "")

def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-flash-latest")

GEMINI_API_KEY = get_gemini_api_key()
GEMINI_MODEL = get_gemini_model()

# Root directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Default dataset path
ORDERS_CSV_PATH = os.getenv("ORDERS_CSV_PATH", str(BASE_DIR / "orders.csv"))

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", 8000))
