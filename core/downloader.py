import logging
import os
import asyncio
from config import TEMP_DIR, MAX_FILE_SIZE, TELEGRAM_BOT_API_LIMIT, USE_MTPROTO_FOR_LARGE_FILES, API_ID, API_HASH, BOT_TOKEN

logger = logging.getLogger(__name__)

# Try to import pyrogram for MTProto support
try:
    from pyrogram import Client
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    logger.warning("Pyrogram not installed. Large file support (>20MB) will be limited.")

# Global pyrogram client
mtproto_client = None

async def init_mtproto_client():
    """Initialize MTProto client for large file downloads."""
    global mtproto_client
    if PYROGRAM_AVAILABLE and USE_MTPROTO_FOR_LARGE_FILES and not mtproto_client:
        try:
            # Create session file directory
            os.makedirs('sessions', exist_ok=True)
            
            mtproto_client = Client(
                name="bot_session",
                api_id=int(API_ID),
                api_hash=API_HASH,
                bot_token=BOT_TOKEN,
                workdir="sessions"
            )
            await mtproto_client.start()
            logger.info("MTProto client initialized for large file support")
        except Exception as e:
            logger.error(f"Failed to initialize MTProto client: {e}")
            mtproto_client = None

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
        
        # Check file size against our maximum limit (2GB)
        if file_size and file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_size_gb = MAX_FILE_SIZE / (1024 * 1024 * 1024)
            logger.error(f"File too large: {size_mb:.1f}MB (Max: {max_size_gb:.1f}GB)")
            
            if status_message:
                await status_message.edit_text(
                    f"❌ **File Too Large!**\n\n"
                    f"📁 Your file: {size_mb:.1f}MB\n"
                    f"📏 Maximum allowed: {max_size_gb:.1f}GB\n\n"
                    f"Please send a smaller file.",
                    parse_mode='Markdown'
                )
            return None
        
        # Determine download method based on file size
        use_mtproto = (file_size and file_size > TELEGRAM_BOT_API_LIMIT and 
                      PYROGRAM_AVAILABLE and USE_MTPROTO_FOR_LARGE_FILES)
        
        if use_mtproto:
            logger.info(f"Using MTProto for large file: {file_size / (1024*1024):.1f}MB")
            return await download_with_mtproto(message, file_obj, file_name, status_message, file_size)
        else:
            logger.info(f"Using Bot API for file: {file_size / (1024*1024):.1f}MB")
            return await download_with_bot_api(message, file_obj, file_name, status_message, file_size)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error downloading media: {error_msg}")
        
        if status_message:
            await status_message.edit_text(f"❌ Download failed: {error_msg}")
        
        return None

async def download_with_bot_api(message, file_obj, file_name, status_message=None, file_size=None):
    """Download file using Bot API (for files <= 20MB)."""
    try:
        # Check Bot API limit
        if file_size and file_size > TELEGRAM_BOT_API_LIMIT:
            size_mb = file_size / (1024 * 1024)
            if status_message:
                await status_message.edit_text(
                    f"❌ File too large for Bot API ({size_mb:.1f}MB > 20MB)\n"
                    f"Switching to MTProto client..."
                )
            return None
        
        # Update status
        if status_message and file_size:
            size_mb = file_size / (1024 * 1024)
            await status_message.edit_text(
                f"📥 Downloading file (Bot API)...\n"
                f"📁 Size: {size_mb:.1f}MB\n"
                f"📄 Name: {file_name[:30]}{'...' if len(file_name) > 30 else ''}"
            )
        
        # Get file and download
        file = await file_obj.get_file()
        file_path = os.path.join(TEMP_DIR, file_name)
        
        start_time = asyncio.get_event_loop().time()
        await file.download_to_drive(file_path)
        download_time = asyncio.get_event_loop().time() - start_time
        
        # Update status
        if status_message:
            size_mb = file_size / (1024 * 1024) if file_size else 0
            speed = size_mb / download_time if download_time > 0 else 0
            await status_message.edit_text(
                f"✅ Download completed (Bot API)!\n"
                f"📁 Size: {size_mb:.1f}MB\n"
                f"⚡ Speed: {speed:.1f}MB/s"
            )
        
        logger.info(f"Downloaded file via Bot API: {file_path}")
        return file_path
        
    except Exception as e:
        if "File is too big" in str(e):
            logger.info("File too big for Bot API, trying MTProto...")
            return await download_with_mtproto(message, file_obj, file_name, status_message, file_size)
        raise e

async def download_with_mtproto(message, file_obj, file_name, status_message=None, file_size=None):
    """Download file using MTProto client (for large files)."""
    try:
        if not PYROGRAM_AVAILABLE:
            if status_message:
                await status_message.edit_text(
                    "❌ Large file support not available.\n"
                    "Install pyrogram: pip install pyrogram"
                )
            return None
        
        # Initialize MTProto client if needed
        await init_mtproto_client()
        
        if not mtproto_client:
            if status_message:
                await status_message.edit_text("❌ Failed to initialize large file client")
            return None
        
        # Update status
        if status_message and file_size:
            size_mb = file_size / (1024 * 1024)
            await status_message.edit_text(
                f"📥 Downloading large file (MTProto)...\n"
                f"📁 Size: {size_mb:.1f}MB\n"
                f"📄 Name: {file_name[:30]}{'...' if len(file_name) > 30 else ''}\n\n"
                f"⏳ This may take a while..."
            )
        
        # Download using pyrogram directly with file_id
        file_path = os.path.join(TEMP_DIR, file_name)
        
        start_time = asyncio.get_event_loop().time()
        
        # Use the file_id from the telegram file object
        file_id = file_obj.file_id
        downloaded_file = await mtproto_client.download_media(
            file_id,
            file_name=file_path
        )
        
        download_time = asyncio.get_event_loop().time() - start_time
        
        # Update status
        if status_message and file_size:
            size_mb = file_size / (1024 * 1024)
            speed = size_mb / download_time if download_time > 0 else 0
            await status_message.edit_text(
                f"✅ Large file download completed!\n"
                f"📁 Size: {size_mb:.1f}MB\n"
                f"⚡ Speed: {speed:.1f}MB/s\n"
                f"⏱️ Time: {download_time:.1f}s"
            )
        
        logger.info(f"Downloaded large file via MTProto: {downloaded_file}")
        return downloaded_file
        
    except Exception as e:
        logger.error(f"MTProto download failed: {e}")
        if status_message:
            await status_message.edit_text(
                f"❌ Large file download failed.\n"
                f"Falling back to Bot API method...\n"
                f"Note: Files >20MB may not work with Bot API."
            )
        # Fallback to Bot API
        return await download_with_bot_api(message, file_obj, file_name, status_message, file_size)

async def download_with_progress(file, file_path, status_message=None, total_size=None):
    """Download file with progress updates."""
    try:
        start_time = asyncio.get_event_loop().time()
        await file.download_to_drive(file_path)
        download_time = asyncio.get_event_loop().time() - start_time
        
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
        max_size_bytes = MAX_FILE_SIZE
    
    return file_size_bytes <= max_size_bytes

def get_max_allowed_size():
    """Get the actual maximum allowed file size."""
    return MAX_FILE_SIZE

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

# Cleanup function
async def cleanup_mtproto_client():
    """Cleanup MTProto client on shutdown."""
    global mtproto_client
    if mtproto_client:
        try:
            await mtproto_client.stop()
            logger.info("MTProto client stopped")
        except Exception as e:
            logger.error(f"Error stopping MTProto client: {e}")
        finally:
            mtproto_client = None
