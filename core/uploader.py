import logging
import os
from telegram import InputMediaVideo, InputMediaDocument

logger = logging.getLogger(__name__)

async def upload_encoded_video(chat_id, file_path, settings, bot, status_message=None):
    """Upload encoded video to Telegram with progress updates."""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Output file not found: {file_path}")
            return False
        
        # Get file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"Uploading file: {file_path} (Size: {file_size_mb:.1f}MB)")
        
        # Update status if message provided
        if status_message:
            await status_message.edit_text(
                f"📤 **Uploading Video**\n\n"
                f"📁 Size: {file_size_mb:.1f}MB\n"
                f"📋 Mode: {settings['upload_mode'].title()}\n"
                f"⏳ Please wait...",
                parse_mode='Markdown'
            )
        
        # Determine upload mode
        if settings['upload_mode'] == 'video':
            success = await upload_as_video(chat_id, file_path, file_size_mb, bot, status_message)
        else:
            success = await upload_as_document(chat_id, file_path, file_size_mb, bot, status_message)
        
        if success:
            logger.info("File uploaded successfully")
            if status_message:
                await status_message.edit_text(
                    f"✅ **Upload Completed!**\n\n"
                    f"📁 Size: {file_size_mb:.1f}MB\n"
                    f"📋 Uploaded as: {settings['upload_mode'].title()}\n"
                    f"🎉 Ready to download!",
                    parse_mode='Markdown'
                )
        else:
            if status_message:
                await status_message.edit_text("❌ Upload failed!")
        
        return success
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        if status_message:
            await status_message.edit_text(f"❌ Upload error: {str(e)}")
        return False

async def upload_as_video(chat_id, file_path, file_size_mb, bot, status_message=None):
    """Upload file as video."""
    try:
        with open(file_path, 'rb') as video_file:
            # Update progress
            if status_message:
                await status_message.edit_text(
                    f"📤 **Uploading as Video**\n\n"
                    f"📁 Size: {file_size_mb:.1f}MB\n"
                    f"🎬 Processing upload...",
                    parse_mode='Markdown'
                )
            
            await bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=f"✅ **Encoded Successfully!**\n\n"
                        f"📁 File size: {file_size_mb:.1f}MB\n"
                        f"🎬 Ready to watch!",
                supports_streaming=True,
                parse_mode='Markdown'
            )
        return True
        
    except Exception as e:
        logger.error(f"Error uploading as video: {e}")
        return False

async def upload_as_document(chat_id, file_path, file_size_mb, bot, status_message=None):
    """Upload file as document."""
    try:
        with open(file_path, 'rb') as document_file:
            # Update progress
            if status_message:
                await status_message.edit_text(
                    f"📤 **Uploading as Document**\n\n"
                    f"📁 Size: {file_size_mb:.1f}MB\n"
                    f"📄 Processing upload...",
                    parse_mode='Markdown'
                )
            
            await bot.send_document(
                chat_id=chat_id,
                document=document_file,
                caption=f"✅ **Encoded Successfully!**\n\n"
                        f"📁 File size: {file_size_mb:.1f}MB\n"
                        f"📄 Ready to download!",
                parse_mode='Markdown'
            )
        return True
        
    except Exception as e:
        logger.error(f"Error uploading as document: {e}")
        return False

async def upload_with_thumbnail(chat_id, file_path, thumbnail_path, settings, bot, status_message=None):
    """Upload video with custom thumbnail."""
    try:
        # Check if files exist
        if not os.path.exists(file_path):
            logger.error(f"Video file not found: {file_path}")
            return False
        
        if not os.path.exists(thumbnail_path):
            logger.warning(f"Thumbnail not found: {thumbnail_path}")
            # Fallback to normal upload
            return await upload_encoded_video(chat_id, file_path, settings, bot, status_message)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Update status
        if status_message:
            await status_message.edit_text(
                f"📤 **Uploading with Thumbnail**\n\n"
                f"📁 Size: {file_size_mb:.1f}MB\n"
                f"🖼️ Custom thumbnail attached\n"
                f"⏳ Processing...",
                parse_mode='Markdown'
            )
        
        # Upload with thumbnail
        with open(file_path, 'rb') as video_file, open(thumbnail_path, 'rb') as thumb_file:
            if settings['upload_mode'] == 'video':
                await bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    thumbnail=thumb_file,
                    caption=f"✅ **Encoded with Custom Thumbnail!**\n\n"
                            f"📁 File size: {file_size_mb:.1f}MB\n"
                            f"🖼️ Custom thumbnail applied",
                    supports_streaming=True,
                    parse_mode='Markdown'
                )
            else:
                # Documents don't support thumbnails in the same way
                await bot.send_document(
                    chat_id=chat_id,
                    document=video_file,
                    caption=f"✅ **Encoded Successfully!**\n\n"
                            f"📁 File size: {file_size_mb:.1f}MB\n"
                            f"📄 Document format",
                    parse_mode='Markdown'
                )
        
        logger.info("File uploaded successfully with thumbnail")
        return True
        
    except Exception as e:
        logger.error(f"Error uploading with thumbnail: {e}")
        # Fallback to normal upload
        return await upload_encoded_video(chat_id, file_path, settings, bot, status_message)

async def upload_with_progress_callback(chat_id, file_path, settings, bot, progress_callback=None):
    """Upload file with custom progress callback (for future use)."""
    try:
        # This function can be enhanced in the future to provide
        # real upload progress tracking using custom upload methods
        
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        if progress_callback:
            await progress_callback(0, f"Starting upload of {file_size_mb:.1f}MB file...")
        
        # For now, use the standard upload method
        success = await upload_encoded_video(chat_id, file_path, settings, bot)
        
        if progress_callback:
            if success:
                await progress_callback(100, "Upload completed successfully!")
            else:
                await progress_callback(-1, "Upload failed!")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in upload with progress: {e}")
        if progress_callback:
            await progress_callback(-1, f"Upload error: {str(e)}")
        return False

def get_upload_file_size_limit(upload_mode):
    """Get file size limit based on upload mode."""
    # Telegram limits for bot uploads
    if upload_mode == 'video':
        return 50 * 1024 * 1024  # 50MB for videos
    else:
        return 50 * 1024 * 1024  # 50MB for documents

def check_upload_size_limit(file_path, upload_mode):
    """Check if file size is within upload limits."""
    try:
        file_size = os.path.getsize(file_path)
        limit = get_upload_file_size_limit(upload_mode)
        return file_size <= limit, file_size, limit
    except Exception as e:
        logger.error(f"Error checking file size: {e}")
        return False, 0, 0

async def handle_large_file_upload(chat_id, file_path, settings, bot, status_message=None):
    """Handle upload of large files (future enhancement)."""
    try:
        # Check file size
        is_within_limit, file_size, limit = check_upload_size_limit(file_path, settings['upload_mode'])
        
        if not is_within_limit:
            file_size_mb = file_size / (1024 * 1024)
            limit_mb = limit / (1024 * 1024)
            
            if status_message:
                await status_message.edit_text(
                    f"❌ **File Too Large for Upload!**\n\n"
                    f"📁 Your file: {file_size_mb:.1f}MB\n"
                    f"📏 Upload limit: {limit_mb:.1f}MB\n\n"
                    f"**Suggestions:**\n"
                    f"• Use higher compression (higher CRF)\n"
                    f"• Lower resolution\n"
                    f"• Split into smaller segments",
                    parse_mode='Markdown'
                )
            return False
        
        # File is within limits, proceed with normal upload
        return await upload_encoded_video(chat_id, file_path, settings, bot, status_message)
        
    except Exception as e:
        logger.error(f"Error handling large file upload: {e}")
        return False
