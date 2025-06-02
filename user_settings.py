# models/user_settings.py
import logging
from database.db import get_db_connection
from config import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

def create_default_settings(user_id):
    """Create default settings for a new user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user settings already exist
        cursor.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return
        
        # Insert default settings
        cursor.execute("""
            INSERT INTO user_settings (
                user_id, upload_mode, resolution, vcodec, bits, crf, 
                aspect_ratio, custom_thumbnail, watermark, auto_rename, metadata_enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            DEFAULT_SETTINGS['upload_mode'],
            DEFAULT_SETTINGS['resolution'],
            DEFAULT_SETTINGS['vcodec'],
            DEFAULT_SETTINGS['bits'],
            DEFAULT_SETTINGS['crf'],
            DEFAULT_SETTINGS['aspect_ratio'],
            DEFAULT_SETTINGS['custom_thumbnail'],
            DEFAULT_SETTINGS['watermark'],
            DEFAULT_SETTINGS['auto_rename'],
            DEFAULT_SETTINGS['metadata_enabled']
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created default settings for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error creating default settings: {e}")

def get_user_settings(user_id):
    """Get user settings from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT upload_mode, resolution, vcodec, bits, crf, aspect_ratio,
                   custom_thumbnail, watermark, auto_rename, metadata_enabled
            FROM user_settings WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'upload_mode': result[0],
                'resolution': result[1],
                'vcodec': result[2],
                'bits': result[3],
                'crf': result[4],
                'aspect_ratio': result[5],
                'custom_thumbnail': result[6],
                'watermark': result[7],
                'auto_rename': result[8],
                'metadata_enabled': result[9]
            }
        else:
            # Create default settings if not found
            create_default_settings(user_id)
            return DEFAULT_SETTINGS
            
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        return DEFAULT_SETTINGS

def update_user_setting(user_id, setting_name, value):
    """Update a specific user setting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = f"UPDATE user_settings SET {setting_name} = ? WHERE user_id = ?"
        cursor.execute(query, (value, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated {setting_name} to {value} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error updating user setting: {e}")

def delete_user_settings(user_id):
    """Delete user settings."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted settings for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error deleting user settings: {e}")
