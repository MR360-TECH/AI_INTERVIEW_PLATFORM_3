import os
import re
import secrets
from dotenv import load_dotenv

load_dotenv()

IS_PRODUCTION = bool(
    os.environ.get("DATABASE_URL")
    or os.environ.get("RENDER")
    or os.environ.get("RAILWAY_ENVIRONMENT")
    or os.environ.get("FLASK_ENV") == "production"
)

SECRET_KEY = os.environ.get("SECRET_KEY") or "supersecretkey_production_fallback_key_2026"

# Admin credentials
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_EMAIL:
    ADMIN_EMAIL = f"admin_{secrets.token_hex(4)}@example.com"

if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = secrets.token_urlsafe(18)
    print(f" * SECURE WARNING: ADMIN_PASSWORD environment variable was not set.")
    print(f" * A random temporary password has been generated for this session: {ADMIN_PASSWORD}")

# Database URL configuration and fallback
db_url = os.environ.get("DATABASE_URL")
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
else:
    db_user = os.environ.get("DB_USER", "root")
    db_pass = os.environ.get("DB_PASSWORD", "1817")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_name = os.environ.get("DB_NAME", "ai_interview_platform")
    db_url = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'

if db_url.startswith("mysql"):
    try:
        import pymysql
        match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^/:]+)(?::(\d+))?/([^?]+)', db_url)
        if match:
            user, password, host, port, db_name_parsed = match.groups()
            port = int(port) if port else 3306
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                port=port,
                connect_timeout=3
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name_parsed}")
            conn.close()
            print(f"Verified/Created MySQL database '{db_name_parsed}' successfully.")
        else:
            raise ValueError("Invalid MySQL URI format")
    except Exception as e:
        print(f"MySQL database connection failed ({e}). Falling back to SQLite.")
        render_persistent_dir = "/var/data"
        if os.environ.get("RENDER") and os.path.exists(render_persistent_dir):
            db_url = f"sqlite:///{os.path.join(render_persistent_dir, 'ai_interview_platform.db')}"
        else:
            db_url = "sqlite:///ai_interview_platform.db"

SQLALCHEMY_DATABASE_URI = db_url
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_ENGINE_OPTIONS = {}
if not db_url.startswith("sqlite"):
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
        'pool_timeout': 20,
        'max_overflow': 5
    }

# File uploads
render_persistent_dir = "/var/data"
if os.environ.get("RENDER") and os.path.exists(render_persistent_dir):
    UPLOAD_FOLDER = os.path.join(render_persistent_dir, 'uploads')
else:
    UPLOAD_FOLDER = 'uploads'

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}

# Google OAuth credentials
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
has_google_oauth = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

# Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-flash-lite-latest"
