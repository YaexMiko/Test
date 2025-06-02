import logging
from datetime import datetime, timedelta
from database.db import get_db_connection

logger = logging.getLogger(__name__)

def add_user_to_db(user_id, username, first_name):
    """Add user to database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            # Update last active time
            cursor.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            conn.close()
            return
        
        # Add new user
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added user {user_id} to database")
        
    except Exception as e:
        logger.error(f"Error adding user to database: {e}")

def get_user_from_db(user_id):
    """Get user from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return user
        
    except Exception as e:
        logger.error(f"Error getting user from database: {e}")
        return None

def get_all_users():
    """Get all users from database - Admin function."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, join_date, last_active, is_banned
            FROM users 
            ORDER BY join_date DESC
        ''')
        users = cursor.fetchall()
        
        conn.close()
        return users
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

def get_user_count():
    """Get total user count."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = FALSE")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
        
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0

def get_recent_users(days=7):
    """Get users who joined in the last N days."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, join_date 
            FROM users 
            WHERE join_date > datetime('now', '-{} days')
            ORDER BY join_date DESC
        '''.format(days))
        users = cursor.fetchall()
        
        conn.close()
        return users
        
    except Exception as e:
        logger.error(f"Error getting recent users: {e}")
        return []

def get_active_users(days=30):
    """Get users active in the last N days."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, last_active 
            FROM users 
            WHERE last_active > datetime('now', '-{} days')
            AND is_banned = FALSE
            ORDER BY last_active DESC
        '''.format(days))
        users = cursor.fetchall()
        
        conn.close()
        return users
        
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        return []

def update_user_activity(user_id):
    """Update user's last active timestamp."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating user activity: {e}")

def ban_user(user_id, admin_id):
    """Ban a user - Admin function."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET is_banned = TRUE WHERE user_id = ?",
            (user_id,)
        )
        
        conn.commit()
        conn.close()
        
        # Log admin action
        from database.db import log_admin_action
        log_admin_action(admin_id, "BAN_USER", f"Banned user {user_id}", user_id)
        
        logger.info(f"User {user_id} banned by admin {admin_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return False

def unban_user(user_id, admin_id):
    """Unban a user - Admin function."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET is_banned = FALSE WHERE user_id = ?",
            (user_id,)
        )
        
        conn.commit()
        conn.close()
        
        # Log admin action
        from database.db import log_admin_action
        log_admin_action(admin_id, "UNBAN_USER", f"Unbanned user {user_id}", user_id)
        
        logger.info(f"User {user_id} unbanned by admin {admin_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        return False

def get_user_stats():
    """Get comprehensive user statistics - Admin function."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = FALSE")
        total_users = cursor.fetchone()[0]
        
        # Users joined today
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE DATE(join_date) = DATE('now') AND is_banned = FALSE
        ''')
        users_today = cursor.fetchone()[0]
        
        # Users joined this week
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE join_date > datetime('now', '-7 days') AND is_banned = FALSE
        ''')
        users_week = cursor.fetchone()[0]
        
        # Active users (last 30 days)
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_active > datetime('now', '-30 days') AND is_banned = FALSE
        ''')
        active_users = cursor.fetchone()[0]
        
        # Banned users
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = TRUE")
        banned_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'users_today': users_today,
            'users_week': users_week,
            'active_users': active_users,
            'banned_users': banned_users
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {
            'total_users': 0,
            'users_today': 0,
            'users_week': 0,
            'active_users': 0,
            'banned_users': 0
        }

def search_users(query):
    """Search users by username or name - Admin function."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, join_date, is_banned
            FROM users 
            WHERE username LIKE ? OR first_name LIKE ?
            ORDER BY join_date DESC
            LIMIT 50
        ''', (f'%{query}%', f'%{query}%'))
        
        users = cursor.fetchall()
        conn.close()
        return users
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return []

def get_user_processing_history(user_id):
    """Get user's video processing history - Admin function."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_name, input_size, output_size, processing_time, status, timestamp
            FROM video_processing_log 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (user_id,))
        
        history = cursor.fetchall()
        conn.close()
        return history
        
    except Exception as e:
        logger.error(f"Error getting user processing history: {e}")
        return []
