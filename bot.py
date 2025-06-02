import asyncio
import logging
import sys
import os
import signal

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

class TelegramBot:
    def __init__(self):
        self.application = None
        self.is_running = False
    
    async def initialize(self):
        """Initialize the bot and database."""
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
            self.application = Application.builder().token(BOT_TOKEN).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", start_command))
            self.application.add_handler(CommandHandler("help", help_command))
            self.application.add_handler(CommandHandler("settings", settings_command))
            
            # Admin commands
            self.application.add_handler(CommandHandler("admin", admin_command))
            self.application.add_handler(CommandHandler("stats", stats_command))
            self.application.add_handler(CommandHandler("users", users_command))
            self.application.add_handler(CommandHandler("broadcast", broadcast_command))
            
            # Callback query handlers
            self.application.add_handler(CallbackQueryHandler(handle_settings_callback, pattern="^(?!admin_).*"))
            self.application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_.*"))
            
            # Message handlers for media
            self.application.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_media))
            
            logger.info("🚀 Video Encode Bot starting...")
            logger.info("📡 Bot is ready to receive files!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def start_polling(self):
        """Start the bot with polling."""
        try:
            if not self.application:
                logger.error("Bot not initialized!")
                return False
            
            # Initialize the application
            await self.application.initialize()
            await self.application.start()
            
            # Start polling manually
            await self.application.updater.start_polling(
                poll_interval=1.0,
                timeout=10,
                bootstrap_retries=5,
                read_timeout=10,
                write_timeout=10,
                connect_timeout=10,
                pool_timeout=10,
                drop_pending_updates=True
            )
            
            self.is_running = True
            logger.info("✅ Bot started successfully!")
            
            # Keep running until stopped
            try:
                while self.is_running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("🛑 Bot polling cancelled")
            
        except Exception as e:
            logger.error(f"❌ Error during polling: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop(self):
        """Stop the bot gracefully."""
        try:
            self.is_running = False
            
            if self.application:
                if self.application.updater.running:
                    await self.application.updater.stop()
                
                await self.application.stop()
                await self.application.shutdown()
            
            # Close MongoDB connection if connected
            if mongodb_manager.connected:
                await mongodb_manager.disconnect()
            
            logger.info("🛑 Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

# Global bot instance
bot_instance = None

async def main():
    """Main function to run the bot."""
    global bot_instance
    
    try:
        bot_instance = TelegramBot()
        
        # Initialize bot
        if not await bot_instance.initialize():
            logger.error("❌ Failed to initialize bot")
            return
        
        # Start polling
        await bot_instance.start_polling()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if bot_instance:
            await bot_instance.stop()

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"🛑 Received signal {signum}, shutting down...")
    if bot_instance:
        asyncio.create_task(bot_instance.stop())

def run_bot():
    """Run the bot with proper event loop handling."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            logger.warning("⚠️ Event loop already running, creating new task")
            # If we're in Jupyter or already have a loop, create a task
            task = loop.create_task(main())
            return task
        except RuntimeError:
            # No loop running, safe to use asyncio.run()
            asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

if __name__ == '__main__':
    run_bot()
