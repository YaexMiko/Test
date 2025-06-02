import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError
from config import (
    DATABASE_PATH, USE_MONGODB, DB_URI, DB_NAME,
    MONGODB_USERS_COLLECTION, MONGODB_SETTINGS_COLLECTION, 
    MONGODB_STATS_COLLECTION, MONGODB_LOGS_COLLECTION, 
    MONGODB_ADMIN_LOGS_COLLECTION, DEFAULT_SETTINGS,
    MONGODB_CONNECTION_TIMEOUT, MONGODB_SERVER_SELECTION_TIMEOUT,
    MONGODB_MAX_POOL_SIZE, MONGODB_MIN_POOL_SIZE
)

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
    
    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(
                DB_URI,
                serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT,
                connectTimeoutMS=MONGODB_CONNECTION_TIMEOUT,
                maxPoolSize=MONGODB_MAX_POOL_SIZE,
                minPoolSize=MONGODB_MIN_POOL_SIZE
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.db = self.client[DB_NAME]
            self.connected = True
            
            # Clean and create indexes
            await self._clean_and_create_indexes()
            
            logger.info(f"✅ MongoDB connected successfully to database: {DB_NAME}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected MongoDB error: {e}")
            self.connected = False
            return False
    
    async def _clean_and_create_indexes(self):
        """Clean duplicate null values and create indexes."""
        try:
            # Clean users collection first
            await self._clean_users_collection()
            
            # Users collection indexes
            users_collection = self.db[MONGODB_USERS_COLLECTION]
            
            # Drop existing indexes if they exist and recreate
            try:
                existing_indexes = await users_collection.list_indexes().to_list(length=None)
                index_names = [idx['name'] for idx in existing_indexes if idx['name'] != '_id_']
                
                for index_name in index_names:
                    try:
                        await users_collection.drop_index(index_name)
                    except:
                        pass
                
                # Create new indexes
                await users_collection.create_index("user_id", unique=True)
                await users_collection.create_index("username")
                await users_collection.create_index("join_date")
                
            except Exception as e:
                logger.warning(f"Error with users indexes: {e}")
            
            # Settings collection indexes
            settings_collection = self.db[MONGODB_SETTINGS_COLLECTION]
            try:
                # Drop and recreate settings indexes
                existing_indexes = await settings_collection.list_indexes().to_list(length=None)
                index_names = [idx['name'] for idx in existing_indexes if idx['name'] != '_id_']
                
                for index_name in index_names:
                    try:
                        await settings_collection.drop_index(index_name)
                    except:
                        pass
                
                await settings_collection.create_index("user_id", unique=True)
                
            except Exception as e:
                logger.warning(f"Error with settings indexes: {e}")
            
            # Logs collection indexes
            logs_collection = self.db[MONGODB_LOGS_COLLECTION]
            try:
                await logs_collection.create_index("user_id")
                await logs_collection.create_index("timestamp")
                await logs_collection.create_index("status")
            except Exception as e:
                logger.warning(f"Error with logs indexes: {e}")
            
            # Admin logs indexes
            admin_logs_collection = self.db[MONGODB_ADMIN_LOGS_COLLECTION]
            try:
                await admin_logs_collection.create_index("admin_id")
                await admin_logs_collection.create_index("timestamp")
            except Exception as e:
                logger.warning(f"Error with admin logs indexes: {e}")
            
            # Stats collection indexes
            stats_collection = self.db[MONGODB_STATS_COLLECTION]
            try:
                await stats_collection.create_index("date")
            except Exception as e:
                logger.warning(f"Error with stats indexes: {e}")
            
            logger.info("📊 MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {e}")
    
    async def _clean_users_collection(self):
        """Clean users collection from null user_id values."""
        try:
            users_collection = self.db[MONGODB_USERS_COLLECTION]
            
            # Remove documents with null user_id
            result = await users_collection.delete_many({"user_id": None})
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned {result.deleted_count} invalid user records")
            
            # Remove documents with missing user_id field
            result = await users_collection.delete_many({"user_id": {"$exists": False}})
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned {result.deleted_count} records missing user_id")
            
            # Remove documents with empty string user_id
            result = await users_collection.delete_many({"user_id": ""})
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned {result.deleted_count} empty user_id records")
            
            # Remove documents with zero user_id
            result = await users_collection.delete_many({"user_id": 0})
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned {result.deleted_count} zero user_id records")
            
        except Exception as e:
            logger.error(f"Error cleaning users collection: {e}")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("MongoDB disconnected")
    
    # User Management Methods
    async def add_user(self, user_id: int, username: str, first_name: str):
        """Add user to MongoDB."""
        try:
            if not self.connected:
                return False
            
            # Validate user_id
            if not user_id or user_id == 0:
                logger.error(f"Invalid user_id: {user_id}")
                return False
            
            user_data = {
                "user_id": int(user_id),  # Ensure it's an integer
                "username": username,
                "first_name": first_name,
                "join_date": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "is_banned": False,
                "total_videos_processed": 0,
                "total_data_processed": 0
            }
            
            # Use upsert to avoid duplicates
            await self.db[MONGODB_USERS_COLLECTION].update_one(
                {"user_id": int(user_id)},
                {"$set": user_data},
                upsert=True
            )
            
            logger.info(f"✅ User {user_id} added to MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user to MongoDB: {e}")
            return False
    
    async def get_user(self, user_id: int):
        """Get user from MongoDB."""
        try:
            if not self.connected:
                return None
            
            user = await self.db[MONGODB_USERS_COLLECTION].find_one({"user_id": int(user_id)})
            return user
            
        except Exception as e:
            logger.error(f"Error getting user from MongoDB: {e}")
            return None
    
    async def get_all_users(self) -> List[Dict]:
        """Get all users from MongoDB."""
        try:
            if not self.connected:
                return []
            
            # Only get users with valid user_id
            cursor = self.db[MONGODB_USERS_COLLECTION].find(
                {"user_id": {"$exists": True, "$ne": None, "$gt": 0}}
            ).sort("join_date", -1)
            users = await cursor.to_list(length=None)
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users from MongoDB: {e}")
            return []
    
    async def get_user_count(self) -> int:
        """Get total user count."""
        try:
            if not self.connected:
                return 0
            
            # Only count users with valid user_id
            count = await self.db[MONGODB_USERS_COLLECTION].count_documents(
                {"user_id": {"$exists": True, "$ne": None, "$gt": 0}}
            )
            return count
            
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0
    
    async def update_user_activity(self, user_id: int):
        """Update user last activity."""
        try:
            if not self.connected:
                return False
            
            await self.db[MONGODB_USERS_COLLECTION].update_one(
                {"user_id": int(user_id)},
                {"$set": {"last_active": datetime.utcnow()}}
            )
            return True
            
        except Exception as e:
            logger.error(f"Error updating user activity: {e}")
            return False
    
    # User Settings Methods
    async def create_user_settings(self, user_id: int):
        """Create default settings for user."""
        try:
            if not self.connected:
                return False
            
            # Validate user_id
            if not user_id or user_id == 0:
                logger.error(f"Invalid user_id for settings: {user_id}")
                return False
            
            settings_data = {
                "user_id": int(user_id),
                **DEFAULT_SETTINGS,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.db[MONGODB_SETTINGS_COLLECTION].update_one(
                {"user_id": int(user_id)},
                {"$set": settings_data},
                upsert=True
            )
            
            logger.info(f"✅ Settings created for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user settings: {e}")
            return False
    
    async def get_user_settings(self, user_id: int):
        """Get user settings."""
        try:
            if not self.connected:
                return DEFAULT_SETTINGS
            
            settings = await self.db[MONGODB_SETTINGS_COLLECTION].find_one({"user_id": int(user_id)})
            
            if settings:
                # Remove MongoDB specific fields
                settings.pop('_id', None)
                settings.pop('created_at', None)
                settings.pop('updated_at', None)
                settings.pop('user_id', None)
                return settings
            else:
                # Create default settings if not found
                await self.create_user_settings(user_id)
                return DEFAULT_SETTINGS
                
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return DEFAULT_SETTINGS
    
    async def update_user_setting(self, user_id: int, setting_name: str, value):
        """Update specific user setting."""
        try:
            if not self.connected:
                return False
            
            await self.db[MONGODB_SETTINGS_COLLECTION].update_one(
                {"user_id": int(user_id)},
                {
                    "$set": {
                        setting_name: value,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ Updated {setting_name} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user setting: {e}")
            return False
    
    # Statistics Methods
    async def log_video_processing(self, user_id: int, file_name: str, input_size: int, 
                                 output_size: int, processing_time: int, status: str, 
                                 error_message: str = None):
        """Log video processing statistics."""
        try:
            if not self.connected:
                return False
            
            log_data = {
                "user_id": int(user_id),
                "file_name": file_name,
                "input_size": input_size,
                "output_size": output_size,
                "processing_time": processing_time,
                "status": status,
                "error_message": error_message,
                "timestamp": datetime.utcnow()
            }
            
            await self.db[MONGODB_LOGS_COLLECTION].insert_one(log_data)
            
            # Update user stats
            if status == "success":
                await self.db[MONGODB_USERS_COLLECTION].update_one(
                    {"user_id": int(user_id)},
                    {
                        "$inc": {
                            "total_videos_processed": 1,
                            "total_data_processed": input_size
                        }
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging video processing: {e}")
            return False
    
    async def log_admin_action(self, admin_id: int, action_type: str, action_details: str, 
                             target_user_id: int = None):
        """Log admin actions."""
        try:
            if not self.connected:
                return False
            
            action_data = {
                "admin_id": int(admin_id),
                "action_type": action_type,
                "action_details": action_details,
                "target_user_id": int(target_user_id) if target_user_id else None,
                "timestamp": datetime.utcnow()
            }
            
            await self.db[MONGODB_ADMIN_LOGS_COLLECTION].insert_one(action_data)
            return True
            
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")
            return False
    
    async def get_processing_stats(self):
        """Get video processing statistics."""
        try:
            if not self.connected:
                return {"total_processed": 0, "success_rate": 0, "avg_processing_time": 0}
            
            # Total processed
            total_processed = await self.db[MONGODB_LOGS_COLLECTION].count_documents({})
            
            # Successful processes
            successful = await self.db[MONGODB_LOGS_COLLECTION].count_documents({"status": "success"})
            
            # Success rate
            success_rate = (successful / total_processed * 100) if total_processed > 0 else 0
            
            # Average processing time
            pipeline = [
                {"$match": {"status": "success"}},
                {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time"}}}
            ]
            
            result = await self.db[MONGODB_LOGS_COLLECTION].aggregate(pipeline).to_list(length=1)
            avg_time = int(result[0]["avg_time"]) if result else 0
            
            return {
                "total_processed": total_processed,
                "success_rate": success_rate,
                "avg_processing_time": avg_time
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {"total_processed": 0, "success_rate": 0, "avg_processing_time": 0}
    
    async def get_user_stats(self):
        """Get user statistics."""
        try:
            if not self.connected:
                return {"total_users": 0, "active_today": 0, "new_today": 0}
            
            total_users = await self.get_user_count()
            
            # Users active today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            active_today = await self.db[MONGODB_USERS_COLLECTION].count_documents({
                "last_active": {"$gte": today_start},
                "user_id": {"$exists": True, "$ne": None, "$gt": 0}
            })
            
            # New users today
            new_today = await self.db[MONGODB_USERS_COLLECTION].count_documents({
                "join_date": {"$gte": today_start},
                "user_id": {"$exists": True, "$ne": None, "$gt": 0}
            })
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "new_today": new_today
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"total_users": 0, "active_today": 0, "new_today": 0}

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()

# SQLite fallback functions
def get_db_connection():
    """Get SQLite database connection - fallback."""
    return sqlite3.connect(DATABASE_PATH)

def init_sqlite_database():
    """Initialize SQLite database tables - fallback."""
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
        
        # Create bot_stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT DEFAULT CURRENT_DATE,
                videos_processed INTEGER DEFAULT 0,
                users_active INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create video_processing_log table
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
        
        # Create admin_actions table
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
        
        conn.commit()
        conn.close()
        
        logger.info("✅ SQLite database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")

async def init_database():
    """Initialize database - MongoDB or SQLite fallback."""
    if USE_MONGODB:
        try:
            success = await mongodb_manager.connect()
            if success:
                return True
            else:
                logger.warning("⚠️ MongoDB failed, falling back to SQLite")
        except Exception as e:
            logger.error(f"MongoDB initialization error: {e}")
            logger.warning("⚠️ Falling back to SQLite")
    
    # SQLite fallback
    init_sqlite_database()
    return False

# Wrapper functions for database operations
async def log_admin_action(admin_id, action_type, action_details, target_user_id=None):
    """Log admin actions."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.log_admin_action(admin_id, action_type, action_details, target_user_id)
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO admin_actions (admin_id, action_type, action_details, target_user_id)
                VALUES (?, ?, ?, ?)
            ''', (admin_id, action_type, action_details, target_user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error logging admin action (SQLite): {e}")
            return False

async def log_video_processing(user_id, file_name, input_size, output_size, processing_time, status, error_message=None):
    """Log video processing statistics."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.log_video_processing(
            user_id, file_name, input_size, output_size, processing_time, status, error_message
        )
    else:
        # SQLite fallback
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
            return True
            
        except Exception as e:
            logger.error(f"Error logging video processing (SQLite): {e}")
            return False

async def get_processing_stats():
    """Get video processing statistics."""
    if USE_MONGODB and mongodb_manager.connected:
        return await mongodb_manager.get_processing_stats()
    else:
        # SQLite fallback
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM video_processing_log")
            total_processed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM video_processing_log WHERE status = 'success'")
            successful = cursor.fetchone()[0]
            success_rate = (successful / total_processed * 100) if total_processed > 0 else 0
            
            cursor.execute("SELECT AVG(processing_time) FROM video_processing_log WHERE status = 'success'")
            avg_time = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_processed': total_processed,
                'success_rate': success_rate,
                'avg_processing_time': int(avg_time)
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats (SQLite): {e}")
            return {'total_processed': 0, 'success_rate': 0, 'avg_processing_time': 0}
