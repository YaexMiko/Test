# database/mongodb.py
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import (
    MONGODB_URL, MONGODB_DATABASE, MONGODB_USERS_COLLECTION, 
    MONGODB_SETTINGS_COLLECTION, MONGODB_STATS_COLLECTION, 
    MONGODB_LOGS_COLLECTION, MONGODB_ADMIN_LOGS_COLLECTION,
    MONGODB_CONNECTION_TIMEOUT, MONGODB_SERVER_SELECTION_TIMEOUT,
    MONGODB_MAX_POOL_SIZE, MONGODB_MIN_POOL_SIZE, DEFAULT_SETTINGS
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
                MONGODB_URL,
                serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT,
                connectTimeoutMS=MONGODB_CONNECTION_TIMEOUT,
                maxPoolSize=MONGODB_MAX_POOL_SIZE,
                minPoolSize=MONGODB_MIN_POOL_SIZE
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DATABASE]
            self.connected = True
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("✅ MongoDB connected successfully")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected MongoDB error: {e}")
            self.connected = False
            return False
    
    async def _create_indexes(self):
        """Create database indexes for better performance."""
        try:
            # Users collection indexes
            users_collection = self.db[MONGODB_USERS_COLLECTION]
            await users_collection.create_index("user_id", unique=True)
            await users_collection.create_index("username")
            await users_collection.create_index("join_date")
            
            # Settings collection indexes
            settings_collection = self.db[MONGODB_SETTINGS_COLLECTION]
            await settings_collection.create_index("user_id", unique=True)
            
            # Logs collection indexes
            logs_collection = self.db[MONGODB_LOGS_COLLECTION]
            await logs_collection.create_index("user_id")
            await logs_collection.create_index("timestamp")
            await logs_collection.create_index("status")
            
            # Admin logs indexes
            admin_logs_collection = self.db[MONGODB_ADMIN_LOGS_COLLECTION]
            await admin_logs_collection.create_index("admin_id")
            await admin_logs_collection.create_index("timestamp")
            
            # Stats collection indexes
            stats_collection = self.db[MONGODB_STATS_COLLECTION]
            await stats_collection.create_index("date")
            
            logger.info("📊 MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {e}")
    
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
            
            user_data = {
                "user_id": user_id,
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
                {"user_id": user_id},
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
            
            user = await self.db[MONGODB_USERS_COLLECTION].find_one({"user_id": user_id})
            return user
            
        except Exception as e:
            logger.error(f"Error getting user from MongoDB: {e}")
            return None
    
    async def get_all_users(self) -> List[Dict]:
        """Get all users from MongoDB."""
        try:
            if not self.connected:
                return []
            
            cursor = self.db[MONGODB_USERS_COLLECTION].find().sort("join_date", -1)
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
            
            count = await self.db[MONGODB_USERS_COLLECTION].count_documents({})
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
                {"user_id": user_id},
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
            
            settings_data = {
                "user_id": user_id,
                **DEFAULT_SETTINGS,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.db[MONGODB_SETTINGS_COLLECTION].update_one(
                {"user_id": user_id},
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
            
            settings = await self.db[MONGODB_SETTINGS_COLLECTION].find_one({"user_id": user_id})
            
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
                {"user_id": user_id},
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
                "user_id": user_id,
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
                    {"user_id": user_id},
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
                "admin_id": admin_id,
                "action_type": action_type,
                "action_details": action_details,
                "target_user_id": target_user_id,
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
                "last_active": {"$gte": today_start}
            })
            
            # New users today
            new_today = await self.db[MONGODB_USERS_COLLECTION].count_documents({
                "join_date": {"$gte": today_start}
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

# Helper functions for compatibility
async def init_mongodb():
    """Initialize MongoDB connection."""
    return await mongodb_manager.connect()

async def close_mongodb():
    """Close MongoDB connection."""
    await mongodb_manager.disconnect()
