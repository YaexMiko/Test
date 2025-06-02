import logging
import os

def setup_logger():
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )
    
    # Disable noisy loggers to reduce spam
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('charset_normalizer').setLevel(logging.WARNING)
    
    # Keep only important logs visible
    logging.getLogger('__main__').setLevel(logging.INFO)
    logging.getLogger('commands').setLevel(logging.INFO)
    logging.getLogger('core').setLevel(logging.INFO)
    logging.getLogger('models').setLevel(logging.INFO)
    logging.getLogger('database').setLevel(logging.INFO)
    logging.getLogger('utils').setLevel(logging.INFO)
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info("Logger setup completed - HTTP logs disabled")
