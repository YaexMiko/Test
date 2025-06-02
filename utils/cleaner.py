# utils/cleaner.py
import os
import logging
import glob
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def cleanup_temp_files(file_paths):
    """Clean up temporary files."""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")

def cleanup_old_files(directory, max_age_hours=24):
    """Clean up files older than specified hours."""
    try:
        if not os.path.exists(directory):
            return
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for file_path in glob.glob(os.path.join(directory, "*")):
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old file: {file_path}")
                    
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")

def get_directory_size(directory):
    """Get total size of directory in bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error calculating directory size: {e}")
    
    return total_size
