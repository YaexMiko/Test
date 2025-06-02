# commands/start.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.users import add_user_to_db
from models.user_settings import create_default_settings

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
    # Add user to database
    add_user_to_db(user.id, user.username, user.first_name)
    
    # Create default settings for user
    create_default_settings(user.id)
    
    welcome_message = f"""
🎬 **Welcome to Video Encode Bot!** 🎬

Hello {user.first_name}! 👋

I'm your personal video encoding assistant. I can help you:
✨ Encode videos with custom settings
📱 Convert between different formats
🎯 Compress videos efficiently
⚙️ Customize encoding parameters

**Available Commands:**
/start - Start the bot
/settings - Configure encoding preferences
/help - Get help and support

Send me any video or document to start encoding!
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )
    
    logger.info(f"User {user.id} started the bot")
