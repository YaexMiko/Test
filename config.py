# config.py - Configuration file
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
API_ID = os.getenv('API_ID', 'YOUR_API_ID')
API_HASH = os.getenv('API_HASH', 'YOUR_API_HASH')

# Database Configuration
DATABASE_PATH = 'bot_database.db'

# Encoding Configuration
DEFAULT_SETTINGS = {
    'upload_mode': 'document',  # document or video
    'resolution': '240',
    'vcodec': 'x265',
    'bits': '10',
    'crf': '30',
    'aspect_ratio': '16:9',
    'custom_thumbnail': None,
    'watermark': None,
    'auto_rename': None,
    'metadata_enabled': False
}

# File paths
TEMP_DIR = 'temp'
THUMBNAILS_DIR = 'thumbnails'
DEFAULT_THUMBNAIL = 'assets/default_thumbnail.jpg'

# FFmpeg settings
FFMPEG_PATH = 'ffmpeg'
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB in bytes
