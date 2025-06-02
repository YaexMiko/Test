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
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE
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
        
        # Create bot_stats table for admin statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT DEFAULT CURRENT_DATE,
                videos_processed INTEGER DEFAULT 0,
                users_active INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                total_uploads INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create video_processing_log for tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_name TEXT,
                input_size INTEGER,
                output_size INTEGER,
                processing_time INTEGER,
                status TEXT,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create admin_actions for audit log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action_type TEXT,
                action_details TEXT,
                target_user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create broadcast_messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcast_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT,
                sent_by INTEGER,
                total_users INTEGER,
                successful_sends INTEGER,
                failed_sends INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully with admin tables")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def log_admin_action(admin_id, action_type, action_details, target_user_id=None):
    """Log admin actions for audit trail."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_actions (admin_id, action_type, action_details, target_user_id)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, action_type, action_details, target_user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin action logged: {action_type} by {admin_id}")
        
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")

def log_video_processing(user_id, file_name, input_size, output_size, processing_time, status, error_message=None):
    """Log video processing statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO video_processing_log 
            (user_id, file_name, input_size, output_size, processing_time, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, file_name, input_size, output_size, processing_time, status, error_message))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Video processing logged: {status} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error logging video processing: {e}")

def update_daily_stats(videos_processed=0, users_active=0, errors_count=0):
    """Update daily statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if today's stats exist
        cursor.execute('''
            SELECT id FROM bot_stats WHERE date = DATE('now')
        ''')
        
        if cursor.fetchone():
            # Update existing record
            cursor.execute('''
                UPDATE bot_stats 
                SET videos_processed = videos_processed + ?,
                    users_active = ?,
                    errors_count = errors_count + ?
                WHERE date = DATE('now')
            ''', (videos_processed, users_active, errors_count))
        else:
            # Create new record
            cursor.execute('''
                INSERT INTO bot_stats (videos_processed, users_active, errors_count)
                VALUES (?, ?, ?)
            ''', (videos_processed, users_active, errors_count))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating daily stats: {e}")

def get_processing_stats():
    """Get video processing statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total processed videos
        cursor.execute("SELECT COUNT(*) FROM video_processing_log")
        total_processed = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute("SELECT COUNT(*) FROM video_processing_log WHERE status = 'success'")
        successful = cursor.fetchone()[0]
        success_rate = (successful / total_processed * 100) if total_processed > 0 else 0
        
        # Average processing time
        cursor.execute("SELECT AVG(processing_time) FROM video_processing_log WHERE status = 'success'")
        avg_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_processed': total_processed,
            'success_rate': success_rate,
            'avg_processing_time': int(avg_time)
        }
        
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        return {'total_processed': 0, 'success_rate': 0, 'avg_processing_time': 0}

def cleanup_old_logs(days=30):
    """Clean up old log entries."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clean old processing logs
        cursor.execute('''
            DELETE FROM video_processing_log 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days))
        
        # Clean old admin actions
        cursor.execute('''
            DELETE FROM admin_actions 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up logs older than {days} days")
        
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {e}")
