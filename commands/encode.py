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
                f"🎨 Quality: CRF {settings['crf']}\n"
                f"💿 Bit depth: {settings['bits']}-bit\n"
                f"📐 Aspect: {settings['aspect_ratio']}\n\n"
                f"⏳ Initializing encoder...",
                parse_mode='Markdown'
            )
        else:
            await status_message.edit_text(
                f"🔄 **Starting Encoding**\n\n"
                f"🎬 Codec: {settings['vcodec']}\n"
                f"📺 Resolution: {settings['resolution']}p\n"
                f"🎨 Quality: CRF {settings['crf']}\n\n"
                f"⏳ Initializing encoder...",
                parse_mode='Markdown'
            )
        
        # Encode the video with progress tracking
        output_path = await encode_video(file_path, settings, status_message)
        
        if not output_path:
            await status_message.edit_text(
                "❌ **Encoding Failed**\n\n"
                "The video encoding process encountered an error.\n"
                "Please try again or check your file format.",
                parse_mode='Markdown'
            )
            cleanup_temp_files([file_path])
            return
        
        # Get encoding statistics
        stats = await get_encoding_stats(output_path)
        if stats and os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            output_size_mb = get_file_size_mb(output_size)
            
            # Calculate compression ratio
            if file_obj and file_obj.file_size:
                input_size_mb = get_file_size_mb(file_obj.file_size)
                compression_ratio = ((file_obj.file_size - output_size) / file_obj.file_size) * 100
                
                await status_message.edit_text(
                    f"✅ **Encoding Completed!**\n\n"
                    f"📊 **Results:**\n"
                    f"📁 Input: {input_size_mb}MB → Output: {output_size_mb}MB\n"
                    f"📉 Compression: {compression_ratio:.1f}% reduced\n"
                    f"🎬 Codec: {stats.get('codec', 'unknown')}\n"
                    f"📺 Resolution: {stats.get('resolution', 'unknown')}\n"
                    f"⏱️ Duration: {stats.get('duration', '00:00:00')}\n"
                    f"📡 Bitrate: {stats.get('bitrate', '0k')}\n\n"
                    f"📤 Preparing upload...",
                    parse_mode='Markdown'
                )
            else:
                await status_message.edit_text(
                    f"✅ **Encoding Completed!**\n\n"
                    f"📁 Output size: {output_size_mb}MB\n"
                    f"🎬 Codec: {stats.get('codec', 'unknown')}\n"
                    f"📺 Resolution: {stats.get('resolution', 'unknown')}\n"
                    f"⏱️ Duration: {stats.get('duration', '00:00:00')}\n\n"
                    f"📤 Preparing upload...",
                    parse_mode='Markdown'
                )
        else:
            # Fallback if we can't get stats
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                output_size_mb = get_file_size_mb(output_size)
                await status_message.edit_text(
                    f"✅ **Encoding Completed!**\n\n"
                    f"📁 Output size: {output_size_mb}MB\n"
                    f"📤 Preparing upload...",
                    parse_mode='Markdown'
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
            # Final success message with summary
            final_stats = ""
            if file_obj and file_obj.file_size and os.path.exists(output_path):
                input_size_mb = get_file_size_mb(file_obj.file_size)
                output_size = os.path.getsize(output_path)
                output_size_mb = get_file_size_mb(output_size)
                compression_ratio = ((file_obj.file_size - output_size) / file_obj.file_size) * 100
                
                final_stats = (
                    f"📊 **Compression Summary:**\n"
                    f"📁 {input_size_mb}MB → {output_size_mb}MB\n"
                    f"📉 {compression_ratio:.1f}% size reduction\n"
                    f"🎬 {settings['vcodec']} @ {settings['resolution']}p\n"
                    f"🎨 CRF {settings['crf']} quality\n\n"
                )
            
            await status_message.edit_text(
                f"🎉 **Processing Complete!**\n\n"
                f"{final_stats}"
                f"✅ Video successfully encoded and uploaded!\n"
                f"📋 Uploaded as: {settings['upload_mode'].title()}\n"
                f"⬇️ Ready to download and enjoy!",
                parse_mode='Markdown'
            )
        else:
            await status_message.edit_text(
                "❌ **Upload Failed**\n\n"
                "The encoding was successful but upload failed.\n"
                "This might be due to file size limits or network issues.\n\n"
                "**Suggestions:**\n"
                "• Try using higher compression (CRF 35+)\n"
                "• Lower the resolution\n"
                "• Check your network connection",
                parse_mode='Markdown'
            )
        
        # Cleanup temporary files
        cleanup_temp_files([file_path, output_path])
        
    except Exception as e:
        logger.error(f"Error processing media: {e}")
        
        # Provide user-friendly error messages
        error_msg = str(e).lower()
        if "no space left" in error_msg:
            user_error = "❌ **Server Storage Full**\n\nPlease try again later."
        elif "timeout" in error_msg:
            user_error = "❌ **Processing Timeout**\n\nFile too large or server busy. Try a smaller file."
        elif "memory" in error_msg:
            user_error = "❌ **Memory Error**\n\nFile too complex to process. Try lower resolution."
        elif "ffmpeg" in error_msg:
            user_error = "❌ **Encoding Error**\n\nUnsupported format or corrupted file."
        else:
            user_error = f"❌ **Processing Error**\n\n{str(e)[:100]}..."
        
        await status_message.edit_text(
            f"{user_error}\n\n"
            f"**Need help?**\n"
            f"• Try /help for guidance\n"
            f"• Check your file format\n"
            f"• Use /settings to adjust quality",
            parse_mode='Markdown'
        )
        
        # Cleanup any temporary files
        cleanup_temp_files([])

async def handle_photo_for_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads for custom thumbnails (future feature)."""
    try:
        user_id = update.effective_user.id
        
        # This function can be expanded in the future to handle
        # custom thumbnail uploads
        
        await update.message.reply_text(
            "📸 **Custom Thumbnail Feature**\n\n"
            "This feature is coming soon!\n"
            "You'll be able to set custom thumbnails for your encoded videos.\n\n"
            "For now, use /settings to configure other options.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error handling photo for thumbnail: {e}")

async def show_encoding_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show encoding help and tips."""
    help_text = """
🎬 **Video Encoding Guide**

**Quality Settings (CRF):**
• 18-23: High quality (larger files)
• 24-28: Good quality (balanced)
• 29-35: Lower quality (smaller files)

**Resolution Guide:**
• 1080p: Best quality, largest files
• 720p: Good balance
• 480p: Smaller files
• 240p: Smallest files, mobile friendly

**Codec Comparison:**
• x264: Faster encoding, wider compatibility
• x265: Better compression, smaller files

**Tips for Better Results:**
• Higher CRF = smaller files, lower quality
• Lower resolution = faster processing
• x265 takes longer but saves space
• 10-bit provides better color depth

**File Size Tips:**
• Large files: Use CRF 30+ and lower resolution
• Quality priority: Use CRF 20-25
• Speed priority: Use x264 codec

Use /settings to adjust these parameters!
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_encoding_queue_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current encoding queue status (future feature)."""
    await update.message.reply_text(
        "📋 **Queue Status**\n\n"
        "Queue management feature coming soon!\n"
        "This will show your current position and estimated wait times.\n\n"
        "Currently processing files one at a time.",
        parse_mode='Markdown'
    )

# Utility functions for the encoding module
def get_encoding_preset(quality_level):
    """Get encoding preset based on quality level."""
    presets = {
        'fast': {'crf': '30', 'preset': 'fast'},
        'balanced': {'crf': '25', 'preset': 'medium'},
        'quality': {'crf': '20', 'preset': 'slow'},
        'archive': {'crf': '18', 'preset': 'veryslow'}
    }
    return presets.get(quality_level, presets['balanced'])

def estimate_file_size(input_size_mb, target_crf, resolution_scale=1.0):
    """Estimate output file size based on settings."""
    # This is a rough estimation
    base_compression = 0.3  # 30% of original size as baseline
    
    # CRF impact (lower CRF = larger files)
    crf_factor = max(0.1, 1.0 - (int(target_crf) - 18) * 0.03)
    
    # Resolution impact
    resolution_factor = resolution_scale ** 2
    
    estimated_size = input_size_mb * base_compression * crf_factor * resolution_factor
    return max(0.1, estimated_size)  # Minimum 0.1MB

def validate_encoding_settings(settings):
    """Validate encoding settings before processing."""
    errors = []
    
    # Validate CRF
    try:
        crf = int(settings.get('crf', 23))
        if crf < 0 or crf > 51:
            errors.append("CRF must be between 0 and 51")
    except ValueError:
        errors.append("CRF must be a valid number")
    
    # Validate resolution
    valid_resolutions = ['240', '360', '480', '576', '720', '1080']
    if settings.get('resolution') not in valid_resolutions:
        errors.append(f"Resolution must be one of: {', '.join(valid_resolutions)}")
    
    # Validate codec
    valid_codecs = ['x264', 'x265']
    if settings.get('vcodec') not in valid_codecs:
        errors.append(f"Codec must be one of: {', '.join(valid_codecs)}")
    
    # Validate bit depth
    valid_bits = ['8', '10']
    if settings.get('bits') not in valid_bits:
        errors.append(f"Bit depth must be one of: {', '.join(valid_bits)}")
    
    return errors

async def handle_batch_encoding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle batch encoding requests (future feature)."""
    await update.message.reply_text(
        "📦 **Batch Encoding**\n\n"
        "Batch processing feature coming soon!\n"
        "You'll be able to process multiple files with the same settings.\n\n"
        "For now, send files one at a time.",
        parse_mode='Markdown'
    )
