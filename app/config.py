import os

class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")  # Pooler 6543 + sslmode=require
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me")
    API_BASE_URL = os.getenv("API_BASE_URL", "")
