import os
import logging

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

def cleanup_temp_directory():
    """Clean up entire temp directory."""
    try:
        temp_dir = 'temp'
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info("Cleaned up temp directory")
    except Exception as e:
        logger.error(f"Error cleaning temp directory: {e}")
