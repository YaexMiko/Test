# utils/timer.py
import asyncio
import logging

logger = logging.getLogger(__name__)

class Timer:
    """Timer utility for timeouts and delays."""
    
    def __init__(self, timeout=60):
        self.timeout = timeout
        self._task = None
    
    async def start(self, callback, *args, **kwargs):
        """Start timer with callback."""
        try:
            await asyncio.sleep(self.timeout)
            await callback(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info("Timer cancelled")
        except Exception as e:
            logger.error(f"Timer error: {e}")
    
    def cancel(self):
        """Cancel timer."""
        if self._task and not self._task.done():
            self._task.cancel()

async def timeout_handler(message, timeout_seconds=60):
    """Handle timeout for user input."""
    try:
        await asyncio.sleep(timeout_seconds)
        await message.edit_text("⏰ Timeout! Please try again.")
    except Exception as e:
        logger.error(f"Timeout handler error: {e}")

def debounce(wait_time):
    """Debounce decorator for functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            await asyncio.sleep(wait_time)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
