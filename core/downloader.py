import logging
import os
import aiohttp
from config import TEMP_DIR

logger = logging.getLogger(__name__)

async def download_media(message, status_message=None):
    """Download media from Telegram message."""
    try:
        # Ensure temp directory exists
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Get file info
        if message.video:
            file_obj = message.video
            file_name = f"video_{message.message_id}.mp4"
        elif message.document:
            file_obj = message.document
            file_name = file_obj.file_name or f"document_{message.message_id}"
        else:
            logger.error("No video or document found in message")
            return None
        
        # Get file
        file = await file_obj.get_file()
        file_path = os.path.join(TEMP_DIR, file_name)
        
        # Download file
        await file.download_to_drive(file_path)
        
        logger.info(f"Downloaded file: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None

async def download_thumbnail(file_id, user_id):
    """Download thumbnail from Telegram."""
    try:
        # Implementation for thumbnail download
        pass
    except Exception as e:
        logger.error(f"Error downloading thumbnail: {e}")
        return None
