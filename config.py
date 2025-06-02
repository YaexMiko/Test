import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Disable HTTP logs at config level too
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8191627683:AAEaD3MzrdkcwhAj6eiATKLAwPzQQhbxVCI')
API_ID = os.getenv('API_ID', '28614709')
API_HASH = os.getenv('API_HASH', 'f36fd2ee6e3d3a17c4d244ff6dc1bac8')

# Owner Configuration - IMPORTANT: Change this to your actual Telegram user ID
OWNER_ID = os.getenv('OWNER_ID', '7970350353')  # Replace with your actual user ID

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

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
ENABLE_HTTP_LOGS = os.getenv('ENABLE_HTTP_LOGS', 'false').lower() == 'true'

# Additional logging filters
if not ENABLE_HTTP_LOGS:
    # Comprehensive list of noisy loggers to silence
    NOISY_LOGGERS = [
        'httpx',
        'httpcore',
        'telegram',
        'urllib3',
        'aiohttp',
        'asyncio',
        'charset_normalizer',
        'multipart',
        'pyrogram',
        'h11',
        'h2',
        'hpack'
    ]
    
    for logger_name in NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

# Bot status messages
BOT_MESSAGES = {
    'start': "🚀 Video Encode Bot starting...",
    'ready': "📡 Bot is ready to receive files!",
    'stop': "🛑 Bot stopped by user",
    'crash': "❌ Bot crashed",
    'download_start': "📥 Downloading file...",
    'download_complete': "✅ Download completed!",
    'encode_start': "🔄 Encoding video...",
    'encode_complete': "✅ Encoding completed!",
    'upload_start': "📤 Uploading video...",
    'upload_complete': "✅ Upload completed!"
}

# Performance settings
CONCURRENT_DOWNLOADS = 3  # Maximum concurrent downloads
CONCURRENT_ENCODES = 2    # Maximum concurrent encodes
MAX_QUEUE_SIZE = 10       # Maximum queue size for pending jobs

# Feature flags
ENABLE_LARGE_FILE_SUPPORT = True
ENABLE_PROGRESS_TRACKING = True
ENABLE_THUMBNAIL_SUPPORT = True
ENABLE_WATERMARK_SUPPORT = False  # Coming soon
ENABLE_METADATA_SUPPORT = False   # Coming soon
ENABLE_AUTO_RENAME = False        # Coming soon

# Debug settings
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'

if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)
elif VERBOSE_LOGGING:
    # Enable more detailed logging for core components
    logging.getLogger('core').setLevel(logging.DEBUG)
    logging.getLogger('commands').setLevel(logging.DEBUG)

# Admin settings
ADMIN_FEATURES = {
    'stats_enabled': True,
    'user_management': True,
    'broadcast_enabled': True,
    'system_monitoring': True
}
