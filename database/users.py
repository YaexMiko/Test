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
