import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
_development_secret = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

class Config:
    SECRET_KEY = _development_secret
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "database.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', str(BASE_DIR / "static" / "uploads"))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'webp'}
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB max upload
