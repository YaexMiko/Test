import logging
import sqlite3
from datetime import datetime
from database.db import get_db_connection, mongodb_manager
from config import USE_MONGODB, DEFAULT_SETTINGS

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
                INSERT INTO users (user_id, username, first_name, join_date, last_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, datetime.utcnow(), datetime.utcnow()))
            
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
            
            cursor.execute('''
                SELECT user_id, username, first_name, join_date, last_active, is_banned
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'join_date': row[3],
                    'last_active': row[4],
                    'is_banned': row[5]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user from SQLite: {e}")
            return None

async def get_all_users():
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
            
            cursor.execute('''
                SELECT user_id, username, first_name, join_date, last_active, is_banned
                FROM users ORDER BY join_date DESC
            ''')
            
            users = cursor.fetchall()
            conn.close()
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users from SQLite: {e}")
            return []

async def get_user_count():
    """Get total user count from database - MongoDB or SQLite."""
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

async def get_recent_users(limit=10):
    """Get recent users from database - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        users = await mongodb_manager.get_all_users()
        # Return first 'limit' users (already sorted by join_date desc)
        recent_users = users[:limit]
        # Convert to tuple format
        user_list = []
        for user in recent_users:
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
            
            cursor.execute('''
                SELECT user_id, username, first_name, join_date, last_active, is_banned
                FROM users ORDER BY join_date DESC LIMIT ?
            ''', (limit,))
            
            users = cursor.fetchall()
            conn.close()
            return users
            
        except Exception as e:
            logger.error(f"Error getting recent users from SQLite: {e}")
            return []

async def update_user_activity(user_id):
    """Update user last activity - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.update_user_activity(user_id)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET last_active = ? WHERE user_id = ?
            ''', (datetime.utcnow(), user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user activity in SQLite: {e}")
            return False

async def ban_user(user_id):
    """Ban a user - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        try:
            await mongodb_manager.db[mongodb_manager.db.get_collection('users')._collection_name].update_one(
                {"user_id": int(user_id)},
                {"$set": {"is_banned": True}}
            )
            return True
        except Exception as e:
            logger.error(f"Error banning user in MongoDB: {e}")
            return False
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET is_banned = 1 WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error banning user in SQLite: {e}")
            return False

async def unban_user(user_id):
    """Unban a user - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        try:
            await mongodb_manager.db[mongodb_manager.db.get_collection('users')._collection_name].update_one(
                {"user_id": int(user_id)},
                {"$set": {"is_banned": False}}
            )
            return True
        except Exception as e:
            logger.error(f"Error unbanning user in MongoDB: {e}")
            return False
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET is_banned = 0 WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error unbanning user in SQLite: {e}")
            return False

async def get_user_settings(user_id):
    """Get user settings - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.get_user_settings(user_id)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT upload_mode, resolution, vcodec, bits, crf, aspect_ratio,
                       custom_thumbnail, watermark, auto_rename, metadata_enabled
                FROM user_settings WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'upload_mode': row[0],
                    'resolution': row[1],
                    'vcodec': row[2],
                    'bits': row[3],
                    'crf': row[4],
                    'aspect_ratio': row[5],
                    'custom_thumbnail': row[6],
                    'watermark': row[7],
                    'auto_rename': row[8],
                    'metadata_enabled': row[9]
                }
            else:
                # Create default settings
                await create_user_settings(user_id)
                return DEFAULT_SETTINGS
                
        except Exception as e:
            logger.error(f"Error getting user settings from SQLite: {e}")
            return DEFAULT_SETTINGS

async def create_user_settings(user_id):
    """Create default user settings - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.create_user_settings(user_id)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_settings 
                (user_id, upload_mode, resolution, vcodec, bits, crf, aspect_ratio, metadata_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 
                  DEFAULT_SETTINGS['upload_mode'],
                  DEFAULT_SETTINGS['resolution'],
                  DEFAULT_SETTINGS['vcodec'],
                  DEFAULT_SETTINGS['bits'],
                  DEFAULT_SETTINGS['crf'],
                  DEFAULT_SETTINGS['aspect_ratio'],
                  DEFAULT_SETTINGS['metadata_enabled']))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating user settings in SQLite: {e}")
            return False

async def update_user_setting(user_id, setting_name, value):
    """Update user setting - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.update_user_setting(user_id, setting_name, value)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # First ensure user settings exist
            cursor.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                await create_user_settings(user_id)
            
            # Update the specific setting
            sql = f"UPDATE user_settings SET {setting_name} = ? WHERE user_id = ?"
            cursor.execute(sql, (value, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user setting in SQLite: {e}")
            return False

async def get_user_stats():
    """Get user statistics - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.get_user_stats()
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Active today (simplified for SQLite)
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE date(last_active) = date('now')
            """)
            active_today = cursor.fetchone()[0]
            
            # New today
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE date(join_date) = date('now')
            """)
            new_today = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'active_today': active_today,
                'new_today': new_today
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats from SQLite: {e}")
            return {'total_users': 0, 'active_today': 0, 'new_today': 0}

async def delete_user(user_id):
    """Delete a user completely - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        try:
            # Delete from users collection
            await mongodb_manager.db['users'].delete_one({"user_id": int(user_id)})
            # Delete user settings
            await mongodb_manager.db['user_settings'].delete_one({"user_id": int(user_id)})
            # Delete user logs
            await mongodb_manager.db['video_processing_logs'].delete_many({"user_id": int(user_id)})
            return True
        except Exception as e:
            logger.error(f"Error deleting user from MongoDB: {e}")
            return False
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Delete user settings
            cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
            # Delete processing logs
            cursor.execute("DELETE FROM video_processing_log WHERE user_id = ?", (user_id,))
            # Delete user
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user from SQLite: {e}")
            return False
