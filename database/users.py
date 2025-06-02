# database/users.py
import logging
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
            conn.close()
            return
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added user {user_id} to database")
        
    except Exception as e:
        logger.error(f"Error adding user to database: {e}")

def get_user_info(user_id):
    """Get user information from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, first_name, join_date, is_active
            FROM users WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'first_name': result[2],
                'join_date': result[3],
                'is_active': result[4]
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return None

def update_user_activity(user_id):
    """Update user's last activity."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET is_active = 1 WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating user activity: {e}")

def get_all_users():
    """Get all users from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, username, first_name FROM users WHERE is_active = 1")
        results = cursor.fetchall()
        conn.close()
        
        return [{'user_id': r[0], 'username': r[1], 'first_name': r[2]} for r in results]
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []
