# bot.py - Main entry point
import asyncio
import logging
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

async def main():
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
    application.add_handler(MessageHandler(filters.VIDEO | filters.DOCUMENT, handle_media))
    
    # Start the bot
    logger.info("Starting bot...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
