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
        
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                'upload_mode': row[1],
                'resolution': row[2],
                'vcodec': row[3],
                'bits': row[4],
                'crf': row[5],
                'aspect_ratio': row[6],
                'custom_thumbnail': row[7],
                'watermark': row[8],
                'auto_rename': row[9],
                'metadata_enabled': bool(row[10])
            }
        else:
            # Return default settings if not found
            return DEFAULT_SETTINGS.copy()
            
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        return DEFAULT_SETTINGS.copy()

def update_user_setting(user_id, setting_key, setting_value):
    """Update a specific user setting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prepare the SQL query
        query = f"UPDATE user_settings SET {setting_key} = ? WHERE user_id = ?"
        cursor.execute(query, (setting_value, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated {setting_key} to {setting_value} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error updating user setting: {e}")
