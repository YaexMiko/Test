# commands/help.py
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    
    help_message = """
🆘 **Help & Support** 🆘

**How to use this bot:**

1️⃣ **Configure Settings:**
   • Use /settings to open encoding preferences
   • Customize resolution, codec, quality, etc.
   • Set custom thumbnails and watermarks

2️⃣ **Encode Videos:**
   • Send any video or document
   • Bot will encode using your settings
   • Download the processed file

3️⃣ **Settings Options:**
   • **Upload Mode:** Document or Video format
   • **Resolution:** 240p to 1080p options
   • **Codec:** x264 or x265
   • **Bits:** 8-bit or 10-bit depth
   • **CRF:** Quality setting (21-40)
   • **Aspect Ratio:** Video dimensions
   • **Thumbnail:** Custom video thumbnail
   • **Watermark:** Add logo/text overlay
   • **Auto Rename:** Automatic file naming

**Supported Formats:**
• Input: MP4, AVI, MKV, MOV, and more
• Output: MP4 (optimized)

**File Size Limits:**
• Maximum file size: 2GB
• Processing time varies by file size

**Need more help?**
Contact: @your_support_username

**Commands:**
/start - Start the bot
/settings - Configure preferences  
/help - Show this help message
"""
    
    await update.message.reply_text(
        help_message,
        parse_mode='Markdown'
    )
    
    logger.info(f"Help requested by user {update.effective_user.id}")
