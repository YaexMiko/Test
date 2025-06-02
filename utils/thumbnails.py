import os
import logging
from config import THUMBNAILS_DIR, DEFAULT_THUMBNAIL

logger = logging.getLogger(__name__)

def get_user_thumbnail_path(user_id):
    """Get user's custom thumbnail path."""
    try:
        custom_path = os.path.join(THUMBNAILS_DIR, f"{user_id}.jpg")
        if os.path.exists(custom_path):
            return custom_path
        
        # Return default thumbnail if exists
        if os.path.exists(DEFAULT_THUMBNAIL):
            return DEFAULT_THUMBNAIL
        
        return None
    except Exception as e:
        logger.error(f"Error getting thumbnail path: {e}")
        return None

def save_user_thumbnail(user_id, file_path):
    """Save user's custom thumbnail."""
    try:
        os.makedirs(THUMBNAILS_DIR, exist_ok=True)
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f"{user_id}.jpg")
        
        # Copy file to thumbnails directory
        import shutil
        shutil.copy2(file_path, thumbnail_path)
        
        logger.info(f"Saved thumbnail for user {user_id}")
        return thumbnail_path
    except Exception as e:
        logger.error(f"Error saving thumbnail: {e}")
        return None

def delete_user_thumbnail(user_id):
    """Delete user's custom thumbnail."""
    try:
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f"{user_id}.jpg")
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            logger.info(f"Deleted thumbnail for user {user_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting thumbnail: {e}")
        return False
