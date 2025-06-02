import logging

logger = logging.getLogger(__name__)

def create_progress_message(progress, total):
    """Create a progress message."""
    percentage = (progress / total) * 100 if total > 0 else 0
    return f"Progress: {percentage:.1f}% ({progress}/{total})"

async def update_progress(message, text):
    """Update progress message."""
    try:
        await message.edit_text(text)
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
