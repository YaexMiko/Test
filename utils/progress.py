# utils/progress.py
import logging
import asyncio

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self, message, total_steps=100):
        self.message = message
        self.total_steps = total_steps
        self.current_step = 0
        self.status_text = ""
    
    async def update(self, step, status="Processing..."):
        """Update progress."""
        try:
            self.current_step = step
            self.status_text = status
            
            progress_percent = (step / self.total_steps) * 100
            progress_bar = self._create_progress_bar(progress_percent)
            
            text = f"{status}\n\n{progress_bar}\n{progress_percent:.1f}%"
            
            await self.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def _create_progress_bar(self, percent, length=20):
        """Create visual progress bar."""
        filled = int(length * percent / 100)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}]"

async def create_progress_message(message, text="Starting..."):
    """Create initial progress message."""
    try:
        return await message.reply_text(text)
    except Exception as e:
        logger.error(f"Error creating progress message: {e}")
        return None

def format_file_size(bytes_size):
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def format_duration(seconds):
    """Format duration in human readable format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
