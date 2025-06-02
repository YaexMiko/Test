import logging
import os
from telegram import InputMediaVideo, InputMediaDocument

logger = logging.getLogger(__name__)

async def upload_encoded_video(chat_id, file_path, settings, bot):
    """Upload encoded video to Telegram."""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Output file not found: {file_path}")
            return False
        
        # Get file size
        file_size = os.path.getsize(file_path)
        logger.info(f"Uploading file: {file_path} (Size: {file_size} bytes)")
        
        # Determine upload mode
        if settings['upload_mode'] == 'video':
            # Upload as video
            with open(file_path, 'rb') as video_file:
                await bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption="✅ Encoded successfully!",
                    supports_streaming=True
                )
        else:
            # Upload as document
            with open(file_path, 'rb') as document_file:
                await bot.send_document(
                    chat_id=chat_id,
                    document=document_file,
                    caption="✅ Encoded successfully!"
                )
        
        logger.info("File uploaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return False

async def upload_with_thumbnail(chat_id, file_path, thumbnail_path, settings, bot):
    """Upload video with custom thumbnail."""
    try:
        # Implementation for uploading with thumbnail
        pass
    except Exception as e:
        logger.error(f"Error uploading with thumbnail: {e}")
        return False
