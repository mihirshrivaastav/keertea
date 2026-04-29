import os
import tempfile
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    # SQLite is stored outside the synced workspace by default to avoid OneDrive lock issues.
    DATA_DIR = Path(os.getenv("TAPRI_DATA_DIR") or (Path(tempfile.gettempdir()) / "TapriData"))
    DB_PATH = DATA_DIR / "tapri.db"
    UPLOAD_DIR = BASE_DIR / "uploads"
    ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    SECRET_KEY = os.getenv("SECRET_KEY", "tapri-dev-secret-change-me")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    STRIPE_SECRET_KEY = None
    RAZORPAY_KEY_ID = None
    RAZORPAY_KEY_SECRET = None
