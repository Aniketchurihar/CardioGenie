"""
CardioGenie Configuration
Universal configuration for all environments
"""

import os

class Config:
    """Universal configuration class for all environments"""
    
    # Database Configuration
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/cardiogenie_production.db")
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # AI Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DOCTOR_CHAT_ID = os.getenv("DOCTOR_CHAT_ID")
    
    # Google Calendar Configuration
    DOCTOR_EMAIL = os.getenv("DOCTOR_EMAIL", "aniket.ch71@gmail.com")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")  # No fallback - force Railway to use env var
    GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    # Debug logging for Railway deployment
    @classmethod
    def debug_config(cls):
        print(f"DEBUG CONFIG - GOOGLE_REDIRECT_URI: {cls.GOOGLE_REDIRECT_URI}")
        print(f"DEBUG CONFIG - Environment GOOGLE_REDIRECT_URI: {os.getenv('GOOGLE_REDIRECT_URI')}")
        return cls.GOOGLE_REDIRECT_URI
    
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Medical Dataset Configuration
    MEDICAL_DATASET_PATH = "docs/Datasetab94d2b.json"
    
    # Conversation Configuration
    MAX_QUESTIONS_PER_SYMPTOM = 4
    MAX_FOLLOW_UP_QUESTIONS = 2
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            "GROQ_API_KEY",
            "TELEGRAM_BOT_TOKEN", 
            "DOCTOR_CHAT_ID",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, you can override specific values here if needed
    # For example: HOST = "your-production-host.com"

# Simple function to get config
def get_config(environment="development"):
    """Get configuration based on environment"""
    if environment == "production":
        return ProductionConfig
    else:
        return DevelopmentConfig 