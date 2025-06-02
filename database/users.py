import logging
from datetime import datetime
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
                return True
            
            # Add new user
            cursor.execute(
                "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added user {user_id} to SQLite database")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user to SQLite database: {e}")
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
            return user
            
        except Exception as e:
            logger.error(f"Error getting user from SQLite database: {e}")
            return None

async def get_all_users():
    """Get all users from database - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        users = await mongodb_manager.get_all_users()
        # Convert MongoDB format to SQLite-like format for compatibility
        converted_users = []
        for user in users:
            converted_users.append([
                user.get('user_id'),
                user.get('username'),
                user.get('first_name'),
                user.get('join_date', '').strftime('%Y-%m-%d %H:%M:%S') if user.get('join_date') else ''
            ])
        return converted_users
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id, username, first_name, join_date FROM users ORDER BY join_date DESC")
            users = cursor.fetchall()
            
            conn.close()
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users from SQLite database: {e}")
            return []

async def get_user_count():
    """Get total user count - MongoDB or SQLite."""
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
    """Get recent users - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        try:
            cursor = mongodb_manager.db[mongodb_manager.db.name].find().sort("join_date", -1).limit(limit)
            users = await cursor.to_list(length=limit)
            return users
        except Exception as e:
            logger.error(f"Error getting recent users from MongoDB: {e}")
            return []
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT user_id, username, first_name, join_date FROM users ORDER BY join_date DESC LIMIT ?", 
                (limit,)
            )
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
            
            cursor.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user activity in SQLite: {e}")
            return False

async def ban_user(user_id, is_banned=True):
    """Ban/unban user - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        try:
            await mongodb_manager.db[mongodb_manager.MONGODB_USERS_COLLECTION].update_one(
                {"user_id": user_id},
                {"$set": {"is_banned": is_banned, "banned_at": datetime.utcnow() if is_banned else None}}
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
            
            cursor.execute(
                "UPDATE users SET is_banned = ? WHERE user_id = ?",
                (is_banned, user_id)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error banning user in SQLite: {e}")
            return False

async def is_user_banned(user_id):
    """Check if user is banned - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        try:
            user = await mongodb_manager.get_user(user_id)
            return user.get('is_banned', False) if user else False
        except Exception as e:
            logger.error(f"Error checking ban status in MongoDB: {e}")
            return False
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            return bool(result[0]) if result else False
            
        except Exception as e:
            logger.error(f"Error checking ban status in SQLite: {e}")
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
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE date(last_active) = date('now')"
            )
            active_today = cursor.fetchone()[0]
            
            # New today
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE date(join_date) = date('now')"
            )
            new_today = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "new_today": new_today
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats from SQLite: {e}")
            return {"total_users": 0, "active_today": 0, "new_today": 0}

async def delete_user(user_id):
    """Delete user from database - MongoDB or SQLite."""
    if USE_MONGODB and mongodb_manager.connected:
        try:
            # Delete from users collection
            await mongodb_manager.db[mongodb_manager.MONGODB_USERS_COLLECTION].delete_one({"user_id": user_id})
            
            # Delete user settings
            await mongodb_manager.db[mongodb_manager.MONGODB_SETTINGS_COLLECTION].delete_one({"user_id": user_id})
            
            logger.info(f"User {user_id} deleted from MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user from MongoDB: {e}")
            return False
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Delete user settings first (foreign key constraint)
            cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User {user_id} deleted from SQLite")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user from SQLite: {e}")
            return False
