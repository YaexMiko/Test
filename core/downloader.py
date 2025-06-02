import logging
import os
import aiohttp
import asyncio
from config import TEMP_DIR, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

# Telegram Bot API file size limits
TELEGRAM_BOT_API_LIMIT = 20 * 1024 * 1024  # 20MB limit for Bot API

async def download_media(message, status_message=None):
    """Download media from Telegram message with file size checks."""
    try:
        # Ensure temp directory exists
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Get file info
        if message.video:
            file_obj = message.video
            file_name = f"video_{message.message_id}.mp4"
            file_size = file_obj.file_size
        elif message.document:
            file_obj = message.document
            file_name = file_obj.file_name or f"document_{message.message_id}"
            file_size = file_obj.file_size
        else:
            logger.error("No video or document found in message")
            return None
        
        # Check file size against Telegram Bot API limit first
        if file_size and file_size > TELEGRAM_BOT_API_LIMIT:
            size_mb = file_size / (1024 * 1024)
            limit_mb = TELEGRAM_BOT_API_LIMIT / (1024 * 1024)
            logger.error(f"File too large for Bot API: {size_mb:.1f}MB (Limit: {limit_mb:.1f}MB)")
            
            if status_message:
                await status_message.edit_text(
                    f"❌ **File Too Large for Bot API!**\n\n"
                    f"📁 Your file: {size_mb:.1f}MB\n"
                    f"📏 Bot API limit: {limit_mb:.1f}MB\n\n"
                    f"**Solutions:**\n"
                    f"• Upload files under {limit_mb:.0f}MB\n"
                    f"• Compress your video first\n"
                    f"• Use lower resolution/quality\n"
                    f"• Split large files into parts\n\n"
                    f"**Note:** This is a Telegram Bot API limitation.",
                    parse_mode='Markdown'
                )
            return None
        
        # Check against our configured limit
        if file_size and file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
            logger.error(f"File too large: {size_mb:.1f}MB (Max: {max_size_mb:.1f}MB)")
            
            if status_message:
                await status_message.edit_text(
                    f"❌ File too large!\n"
                    f"📁 File size: {size_mb:.1f}MB\n"
                    f"📏 Maximum allowed: {max_size_mb:.1f}MB\n\n"
                    f"Please send a smaller file or compress it first."
                )
            return None
        
        # Update status with file info
        if status_message and file_size:
            size_mb = file_size / (1024 * 1024)
            await status_message.edit_text(
                f"📥 Downloading file...\n"
                f"📁 Size: {size_mb:.1f}MB\n"
                f"📄 Name: {file_name[:30]}{'...' if len(file_name) > 30 else ''}"
            )
        
        # Get file
        file = await file_obj.get_file()
        file_path = os.path.join(TEMP_DIR, file_name)
        
        # Download file with progress tracking
        await download_with_progress(file, file_path, status_message, file_size)
        
        logger.info(f"Downloaded file: {file_path}")
        return file_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error downloading media: {error_msg}")
        
        # Handle specific Telegram errors
        if "File is too big" in error_msg or "file is too large" in error_msg.lower():
            if status_message:
                await status_message.edit_text(
                    f"❌ **File Too Large!**\n\n"
                    f"This file exceeds Telegram's download limits.\n\n"
                    f"**Solutions:**\n"
                    f"• Upload files under 20MB\n"
                    f"• Compress your video first\n"
                    f"• Use a video compressor app\n"
                    f"• Split large files into smaller parts\n\n"
                    f"**Technical limit:** Telegram Bot API = 20MB",
                    parse_mode='Markdown'
                )
        else:
            if status_message:
                await status_message.edit_text(f"❌ Download failed: {error_msg}")
        
        return None

async def download_with_progress(file, file_path, status_message=None, total_size=None):
    """Download file with progress updates."""
    try:
        # Start download
        start_time = asyncio.get_event_loop().time()
        
        # Simple download without progress for now
        await file.download_to_drive(file_path)
        
        # Calculate download time
        download_time = asyncio.get_event_loop().time() - start_time
        
        # Update status after download
        if status_message and total_size:
            size_mb = total_size / (1024 * 1024)
            speed_mbps = size_mb / download_time if download_time > 0 else 0
            
            await status_message.edit_text(
                f"✅ Download completed!\n"
                f"📁 Size: {size_mb:.1f}MB\n"
                f"⚡ Speed: {speed_mbps:.1f}MB/s\n"
                f"⏱️ Time: {download_time:.1f}s"
            )
        elif status_message:
            await status_message.edit_text("✅ Download completed!")
            
    except Exception as e:
        logger.error(f"Error in download_with_progress: {e}")
        raise e

async def download_thumbnail(file_id, user_id):
    """Download thumbnail from Telegram."""
    try:
        # Create thumbnails directory if it doesn't exist
        os.makedirs('thumbnails', exist_ok=True)
        
        # Implementation for thumbnail download
        # This would typically involve getting the file and saving it
        logger.info(f"Downloading thumbnail for user {user_id}")
        
        # Placeholder implementation
        return None
        
    except Exception as e:
        logger.error(f"Error downloading thumbnail: {e}")
        return None

def get_file_size_mb(file_size_bytes):
    """Convert bytes to MB with 1 decimal place."""
    if file_size_bytes:
        return round(file_size_bytes / (1024 * 1024), 1)
    return 0

def get_file_size_gb(file_size_bytes):
    """Convert bytes to GB with 2 decimal places."""
    if file_size_bytes:
        return round(file_size_bytes / (1024 * 1024 * 1024), 2)
    return 0

def check_file_size_limit(file_size_bytes, max_size_bytes=None):
    """Check if file size is within limits."""
    if max_size_bytes is None:
        max_size_bytes = min(MAX_FILE_SIZE, TELEGRAM_BOT_API_LIMIT)
    
    return file_size_bytes <= max_size_bytes

def get_max_allowed_size():
    """Get the actual maximum allowed file size considering all limits."""
    return min(MAX_FILE_SIZE, TELEGRAM_BOT_API_LIMIT)

def format_file_size(file_size_bytes):
    """Format file size in human readable format."""
    if file_size_bytes is None:
        return "Unknown"
    
    if file_size_bytes < 1024:
        return f"{file_size_bytes} B"
    elif file_size_bytes < 1024 * 1024:
        return f"{file_size_bytes / 1024:.1f} KB"
    elif file_size_bytes < 1024 * 1024 * 1024:
        return f"{file_size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{file_size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_estimated_encoding_time(file_size_mb, resolution):
    """Estimate encoding time based on file size and resolution."""
    # These are rough estimates and will vary based on hardware
    base_time_per_mb = {
        '240': 0.5,   # seconds per MB
        '360': 0.8,
        '480': 1.2,
        '576': 1.5,
        '720': 2.0,
        '1080': 3.0
    }
    
    multiplier = base_time_per_mb.get(str(resolution), 1.0)
    estimated_seconds = file_size_mb * multiplier
    
    if estimated_seconds < 60:
        return f"{int(estimated_seconds)} seconds"
    elif estimated_seconds < 3600:
        return f"{int(estimated_seconds / 60)} minutes"
    else:
        hours = int(estimated_seconds / 3600)
        minutes = int((estimated_seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

async def cleanup_failed_download(file_path):
    """Clean up partially downloaded files."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up failed download: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up failed download: {e}")
