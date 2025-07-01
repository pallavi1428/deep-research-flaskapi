import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    UPLOAD_FOLDER = 'storage/reports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Create directories if they don't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)