import asyncio
import logging
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Disable HTTP logs immediately before other imports
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, USE_MONGODB
from commands.start import start_command
from commands.help import help_command
from commands.settings import settings_command, handle_settings_callback
from commands.admin import admin_command, stats_command, users_command, handle_admin_callback, broadcast_command
from commands.encode import handle_media
from database.db import init_database, mongodb_manager
from utils.logger import setup_logger

# Setup logging
setup_logger()

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot."""
    application = None
    try:
        # Initialize database
        db_success = await init_database()
        
        if USE_MONGODB:
            if db_success:
                logger.info("🗄️ Database: MongoDB")
            else:
                logger.info("🗄️ Database: SQLite (fallback)")
        else:
            logger.info("🗄️ Database: SQLite")
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("settings", settings_command))
        
        # Admin commands
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("users", users_command))
        application.add_handler(CommandHandler("broadcast", broadcast_command))
        
        # Callback query handlers
        application.add_handler(CallbackQueryHandler(handle_settings_callback, pattern="^(?!admin_).*"))
        application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_.*"))
        
        # Message handlers for media
        application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_media))
        
        # Start the bot
        logger.info("🚀 Video Encode Bot starting...")
        logger.info("📡 Bot is ready to receive files!")
        
        # Run the bot with polling
        await application.run_polling(
            poll_interval=0.0,
            timeout=10,
            bootstrap_retries=5,
            read_timeout=5,
            write_timeout=5,
            connect_timeout=5,
            pool_timeout=5,
            drop_pending_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed during startup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            # Close MongoDB connection if connected
            if mongodb_manager.connected:
                await mongodb_manager.disconnect()
            
            logger.info("🛑 Bot shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def run_bot():
    """Run the bot with proper event loop handling."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

if __name__ == '__main__':
    run_bot()
