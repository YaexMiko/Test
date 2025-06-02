import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from core.downloader import download_media, get_file_size_mb
from core.ffmpeg import encode_video, get_encoding_stats
from core.uploader import upload_encoded_video
from models.user_settings import get_user_settings
from utils.progress import create_progress_message
from utils.cleaner import cleanup_temp_files
from config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming media files for encoding."""
    user_id = update.effective_user.id
    
    # Get user settings
    settings = get_user_settings(user_id)
    
    # Check file size before proceeding
    file_obj = update.message.video or update.message.document
    if file_obj and file_obj.file_size:
        file_size_mb = get_file_size_mb(file_obj.file_size)
        max_size_mb = get_file_size_mb(MAX_FILE_SIZE)
        
        if file_obj.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ **File Too Large!**\n\n"
                f"📁 Your file: {file_size_mb}MB\n"
                f"📏 Maximum allowed: {max_size_mb}MB\n\n"
                f"**Suggestions:**\n"
                f"• Compress your video first\n"
                f"• Use a lower resolution/quality\n"
                f"• Split large files into smaller parts\n"
                f"• Try uploading via Telegram Desktop for larger files",
                parse_mode='Markdown'
            )
            return
    
    # Send initial message
    status_message = await update.message.reply_text("📥 Preparing to download...")
    
    try:
        # Download the media file
        file_path = await download_media(update.message, status_message)
        
        if not file_path:
            await status_message.edit_text("❌ Failed to download file.")
            return
        
        # Get file info for better progress tracking
        if file_obj and file_obj.file_size:
            input_size_mb = get_file_size_mb(file_obj.file_size)
            await status_message.edit_text(
                f"🔄 **Starting Encoding**\n\n"
                f"📁 Input size: {input_size_mb}MB\n"
                f"🎬 Codec: {settings['vcodec']}\n"
                f"📺 Resolution: {settings['resolution']}p\n"
                f"🎨 Quality: CRF {settings['crf']}\n\n"
                f"⏳ Initializing encoder...",
                parse_mode='Markdown'
            )
        
        # Encode the video with progress tracking
        output_path = await encode_video(file_path, settings, status_message)
        
        if not output_path:
            await status_message.edit_text("❌ Failed to encode video.")
            cleanup_temp_files([file_path])
            return
        
        # Get encoding statistics
        stats = await get_encoding_stats(output_path)
        if stats and os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            output_size_mb = get_file_size_mb(output_size)
            
            # Calculate compression ratio
            if file_obj and file_obj.file_size:
                compression_ratio = ((file_obj.file_size - output_size) / file_obj.file_size) * 100
                
                await status_message.edit_text(
                    f"✅ **Encoding Completed!**\n\n"
                    f"📁 Output size: {output_size_mb}MB\n"
                    f"📊 Compression: {compression_ratio:.1f}%\n"
                    f"🎬 Codec: {stats.get('codec', 'unknown')}\n"
                    f"📺 Resolution: {stats.get('resolution', 'unknown')}\n"
                    f"⏱️ Duration: {stats.get('duration', '00:00:00')}\n\n"
                    f"📤 Uploading...",
                    parse_mode='Markdown'
                )
            else:
                await status_message.edit_text(
                    f"📤 Uploading encoded video...\n"
                    f"📁 Output size: {output_size_mb}MB"
                )
        
        # Upload the encoded video
        success = await upload_encoded_video(
            update.message.chat_id,
            output_path,
            settings,
            context.bot,
            status_message
        )
        
        if success:
            await status_message.edit_text(
                f"🎉 **Encoding Successful!**\n\n"
                f"✅ Video processed and uploaded\n"
                f"📁 Final size: {output_size_mb}MB\n"
                f"🎬 Quality: {settings['vcodec']} @ {settings['resolution']}p"
            )
        else:
            await status_message.edit_text("❌ Failed to upload encoded video.")
        
        # Cleanup temporary files
        cleanup_temp_files([file_path, output_path])
        
    except Exception as e:
        logger.error(f"Error processing media: {e}")
        await status_message.edit_text(f"❌ Error: {str(e)}")
        
        # Cleanup any temporary files
        cleanup_temp_files([])
