import asyncio
import logging

logger = logging.getLogger(__name__)

class Timer:
    """Timer utility for timeouts."""
    
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self._task = None

    async def start(self):
        """Start the timer."""
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        """Run the timer."""
        try:
            await asyncio.sleep(self.timeout)
            await self.callback()
        except asyncio.CancelledError:
            pass

    def cancel(self):
        """Cancel the timer."""
        if self._task:
            self._task.cancel()
