# config.py - Configuration file
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8191627683:AAEaD3MzrdkcwhAj6eiATKLAwPzQQhbxVCI')
API_ID = os.getenv('API_ID', '28614709')
API_HASH = os.getenv('API_HASH', 'f36fd2ee6e3d3a17c4d244ff6dc1bac8')

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
DEFAULT_THUMBNAIL = 'https://telegra.ph/file/37985c408b1b7c817cbd6-4b850ca6f02b6eae30.jpg'

# FFmpeg settings
FFMPEG_PATH = 'ffmpeg'

# File size limits (in bytes)
TELEGRAM_BOT_API_LIMIT = 20 * 1024 * 1024  # 20MB - Bot API limit
TELEGRAM_CLIENT_LIMIT = 2000 * 1024 * 1024  # 2GB - MTProto client limit
MAX_FILE_SIZE = TELEGRAM_CLIENT_LIMIT  # 2GB using MTProto client
MAX_UPLOAD_SIZE = 50 * 1024 * 1024   # 50MB for uploads via bot

# File size limits for different download methods
DOWNLOAD_LIMITS = {
    'bot_api': TELEGRAM_BOT_API_LIMIT,    # 20MB
    'mtproto': TELEGRAM_CLIENT_LIMIT,     # 2GB
}

# Alternative file size limits for different file types
FILE_SIZE_LIMITS = {
    'video': TELEGRAM_CLIENT_LIMIT,      # 2GB for videos
    'document': TELEGRAM_CLIENT_LIMIT,   # 2GB for documents
    'photo': 10 * 1024 * 1024,          # 10MB for photos
}

# Encoding presets for different quality levels
ENCODING_PRESETS = {
    'ultra_fast': {
        'preset': 'ultrafast',
        'crf': '35'
    },
    'fast': {
        'preset': 'fast',
        'crf': '28'
    },
    'medium': {
        'preset': 'medium',
        'crf': '23'
    },
    'slow': {
        'preset': 'slow',
        'crf': '20'
    }
}

# Progress update intervals
PROGRESS_UPDATE_INTERVAL = 5  # seconds

# Timeout settings
DOWNLOAD_TIMEOUT = 300  # 5 minutes
ENCODING_TIMEOUT = 1800  # 30 minutes
UPLOAD_TIMEOUT = 600    # 10 minutes

# MTProto client settings
USE_MTPROTO_FOR_LARGE_FILES = True
MTPROTO_SESSION_STRING = 'bot_session'
