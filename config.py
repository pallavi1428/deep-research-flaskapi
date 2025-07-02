import os
from dotenv import load_dotenv

load_dotenv()

# Top-level variables so they can be imported
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
CUSTOM_MODEL = os.getenv("CUSTOM_MODEL", "gpt-4o")  # Or whatever your default should be
CONTEXT_SIZE = 8192

if not OPENAI_KEY:
    raise ValueError("OPENAI_KEY is not set. Please set it in your .env file.")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FIRECRAWL_KEY = os.getenv('FIRECRAWL_KEY')
    UPLOAD_FOLDER = 'storage/uploads'
    OUTPUT_FOLDER = 'storage/outputs'
    ALLOWED_EXTENSIONS = {'pdf'}
    PDF_FONT_PATH = 'D:\deep-research-flaskapi\deep-research-api\api\fonts\DejaVuSans-Oblique.ttf'