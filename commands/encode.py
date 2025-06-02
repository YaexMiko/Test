# commands/encode.py
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from core.downloader import download_media
from core.ffmpeg import encode_video
from core.uploader import upload_encoded_video
from models.user_settings import get_user_settings
from utils.progress import create_progress_message
from utils.cleaner import cleanup_temp_files

logger = logging.getLogger(__name__)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming media files for encoding."""
    user_id = update.effective_user.id
    
    # Get user settings
    settings = get_user_settings(user_id)
    
    # Send initial message
    status_message = await update.message.reply_text("📥 Downloading file...")
    
    try:
        # Download the media file
        file_path = await download_media(update.message, status_message)
        
        if not file_path:
            await status_message.edit_text("❌ Failed to download file.")
            return
        
        # Update status
        await status_message.edit_text("🔄 Encoding video...")
        
        # Encode the video
        output_path = await encode_video(file_path, settings, status_message)
        
        if not output_path:
            await status_message.edit_text("❌ Failed to encode video.")
            cleanup_temp_files([file_path])
            return
        
        # Update status
        await status_message.edit_text("📤 Uploading encoded video...")
        
        # Upload the encoded video
        success = await upload_encoded_video(
            update.message.chat_id,
            output_path,
            settings,
            context.bot
        )
        
        if success:
            await status_message.edit_text("✅ Video encoded and uploaded successfully!")
        else:
            await status_message.edit_text("❌ Failed to upload encoded video.")
        
        # Cleanup temporary files
        cleanup_temp_files([file_path, output_path])
        
    except Exception as e:
        logger.error(f"Error processing media: {e}")
        await status_message.edit_text(f"❌ Error: {str(e)}")
        
        # Cleanup any temporary files
        cleanup_temp_files([])
