import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'skillswap-super-secret-key-change-in-prod-2026')
    
    # Database Configuration:
    # Default to SQLite for zero-configuration, instant execution.
    # If DATABASE_URL is set (e.g. mysql+pymysql://root:@localhost/skillswap_db), it will use MySQL.
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        mysql_user = os.environ.get('MYSQL_USER')
        if mysql_user:
            mysql_password = os.environ.get('MYSQL_PASSWORD', '')
            mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
            mysql_db = os.environ.get('MYSQL_DB', 'skillswap_db')
            database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
        else:
            database_url = f"sqlite:///{os.path.join(BASE_DIR, 'skillswap.db')}"
            
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyCWzA1v6aBbq7AgLYXG38S1z3n4hnjxKrk')
    GEMINI_API_URL = os.environ.get(
        'GEMINI_API_URL',
        'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent'
    )
