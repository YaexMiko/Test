import asyncio
import logging
import sys
import os
import signal

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from commands.start import start_command
from commands.help import help_command
from commands.settings import settings_command, handle_settings_callback
from commands.encode import handle_media
from database.db import init_database
from utils.logger import setup_logger

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Initialize database
    init_database()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    
    # Callback query handler for settings
    application.add_handler(CallbackQueryHandler(handle_settings_callback))
    
    # Message handlers for media
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_media))
    
    # Start the bot
    logger.info("Starting bot...")
    
    # Use run_polling without asyncio.run()
    application.run_polling(
        poll_interval=0.0,
        timeout=10,
        bootstrap_retries=5,
        read_timeout=5,
        write_timeout=5,
        connect_timeout=5,
        pool_timeout=5,
    )

if __name__ == '__main__':
    main()
