import logging
from database.db import get_db_connection, mongodb_manager
from config import USE_MONGODB

logger = logging.getLogger(__name__)

async def add_user_to_db(user_id, username, first_name):
    """Add user to database - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.add_user(user_id, username, first_name)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                conn.close()
                return True  # User already exists
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ User {user_id} added to SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user to SQLite: {e}")
            return False

async def get_user_from_db(user_id):
    """Get user from database - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.get_user(user_id)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'first_name': user[2],
                    'join_date': user[3],
                    'last_active': user[4],
                    'is_banned': user[5]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user from SQLite: {e}")
            return None

async def get_all_users_from_db():
    """Get all users from database - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        users = await mongodb_manager.get_all_users()
        # Convert MongoDB format to tuple format for compatibility
        user_list = []
        for user in users:
            user_tuple = (
                user.get('user_id'),
                user.get('username'),
                user.get('first_name'),
                user.get('join_date'),
                user.get('last_active'),
                user.get('is_banned', False)
            )
            user_list.append(user_tuple)
        return user_list
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users ORDER BY join_date DESC")
            users = cursor.fetchall()
            conn.close()
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users from SQLite: {e}")
            return []

async def get_user_count_from_db():
    """Get total user count from database."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.get_user_count()
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting user count from SQLite: {e}")
            return 0

async def update_user_activity_in_db(user_id):
    """Update user last activity in database."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.update_user_activity(user_id)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user activity in SQLite: {e}")
            return False

# User Settings Functions
async def create_user_settings_in_db(user_id):
    """Create default settings for user in database."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.create_user_settings(user_id)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if settings already exist
            cursor.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                conn.close()
                return True  # Settings already exist
            
            # Insert default settings
            cursor.execute('''
                INSERT INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Settings created for user {user_id} in SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user settings in SQLite: {e}")
            return False

async def get_user_settings_from_db(user_id):
    """Get user settings from database."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.get_user_settings(user_id)
    else:
        # SQLite fallback
        try:
            from config import DEFAULT_SETTINGS
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
            settings = cursor.fetchone()
            conn.close()
            
            if settings:
                return {
                    'upload_mode': settings[1] or DEFAULT_SETTINGS['upload_mode'],
                    'resolution': settings[2] or DEFAULT_SETTINGS['resolution'],
                    'vcodec': settings[3] or DEFAULT_SETTINGS['vcodec'],
                    'bits': settings[4] or DEFAULT_SETTINGS['bits'],
                    'crf': settings[5] or DEFAULT_SETTINGS['crf'],
                    'aspect_ratio': settings[6] or DEFAULT_SETTINGS['aspect_ratio'],
                    'custom_thumbnail': settings[7],
                    'watermark': settings[8],
                    'auto_rename': settings[9],
                    'metadata_enabled': bool(settings[10]) if settings[10] is not None else DEFAULT_SETTINGS['metadata_enabled']
                }
            else:
                # Create default settings
                await create_user_settings_in_db(user_id)
                return DEFAULT_SETTINGS
                
        except Exception as e:
            logger.error(f"Error getting user settings from SQLite: {e}")
            from config import DEFAULT_SETTINGS
            return DEFAULT_SETTINGS

async def update_user_setting_in_db(user_id, setting_name, value):
    """Update specific user setting in database."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.update_user_setting(user_id, setting_name, value)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # First ensure settings exist
            cursor.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                # Create settings first
                cursor.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
            
            # Update the specific setting
            query = f"UPDATE user_settings SET {setting_name} = ? WHERE user_id = ?"
            cursor.execute(query, (value, user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Updated {setting_name} for user {user_id} in SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user setting in SQLite: {e}")
            return False
