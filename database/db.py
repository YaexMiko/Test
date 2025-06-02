import sqlite3
import logging
import os
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DATABASE_PATH)

def init_database():
    """Initialize database tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user_settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                upload_mode TEXT DEFAULT 'document',
                resolution TEXT DEFAULT '240',
                vcodec TEXT DEFAULT 'x265',
                bits TEXT DEFAULT '10',
                crf TEXT DEFAULT '30',
                aspect_ratio TEXT DEFAULT '16:9',
                custom_thumbnail TEXT,
                watermark TEXT,
                auto_rename TEXT,
                metadata_enabled BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
