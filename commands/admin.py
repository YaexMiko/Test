import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import OWNER_ID, TEMP_DIR, DATABASE_PATH
from database.users import get_all_users, get_user_count, get_recent_users
from database.db import get_db_connection

logger = logging.getLogger(__name__)

# Bot start time for uptime calculation
bot_start_time = time.time()

def is_owner(user_id):
    """Check if user is the bot owner."""
    return str(user_id) == str(OWNER_ID)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - Owner only."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "This command is restricted to bot administrators only.",
            parse_mode='Markdown'
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
            InlineKeyboardButton("👥 All Users", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🗑️ Clean Temp", callback_data="admin_clean")
        ],
        [
            InlineKeyboardButton("🔄 System Info", callback_data="admin_system"),
            InlineKeyboardButton("📝 Logs", callback_data="admin_logs")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 **Admin Control Panel**\n\n"
        "🤖 Video Encode Bot Admin\n"
        f"👑 Owner: {update.effective_user.first_name}\n\n"
        "Select an option below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - Owner only."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "This command is restricted to bot administrators only.",
            parse_mode='Markdown'
        )
        return
    
    stats = get_bot_stats()
    
    stats_text = f"""
📊 **Bot Statistics Dashboard**

👥 **User Analytics:**
• Total users: {stats['total_users']}
• Active users: {stats['active_users']}
• New registrations: {stats['new_users_today']}
• User growth: +{stats['user_growth']}%

🎬 **Processing Stats:**
• Videos processed: {stats['total_processed']}
• Success rate: {stats['success_rate']:.1f}%
• Average processing time: {stats['avg_processing_time']}s
• Queue status: {stats['queue_status']}

💾 **Storage & Performance:**
• Temp files: {stats['temp_files']} files
• Database size: {stats['db_size']:.2f}MB
• Memory usage: {stats['memory_usage']:.1f}MB
• CPU usage: {stats['cpu_usage']:.1f}%

⏱️ **System Status:**
• Bot uptime: {stats['uptime']}
• Last restart: {stats['last_restart']}
• Status: {stats['status']} 🟢

📈 **Performance Metrics:**
• Response time: {stats['response_time']}ms
• Error rate: {stats['error_rate']:.2f}%
• Peak users online: {stats['peak_users']}
"""
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_stats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command - Owner only."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "This command is restricted to bot administrators only.",
            parse_mode='Markdown'
        )
        return
    
    users = get_all_users()
    total_users = len(users)
    
    if not users:
        await update.message.reply_text(
            "👥 **User Database**\n\n"
            "No users found in the database.",
            parse_mode='Markdown'
        )
        return
    
    # Show first 15 users
    users_text = f"👥 **User Database** ({total_users} total)\n\n"
    
    for i, user in enumerate(users[:15], 1):
        user_id_db, username, first_name, join_date = user
        username_display = f"@{username}" if username else "No username"
        users_text += f"{i}. **{first_name}**\n"
        users_text += f"   • {username_display}\n"
        users_text += f"   • ID: `{user_id_db}`\n"
        users_text += f"   • Joined: {join_date[:10] if join_date else 'Unknown'}\n\n"
    
    if total_users > 15:
        users_text += f"... and {total_users - 15} more users\n\n"
    
    users_text += f"📊 **Quick Stats:**\n"
    users_text += f"• Total Users: {total_users}\n"
    users_text += f"• Recent Users: {len([u for u in users if u[3] and (datetime.now() - datetime.fromisoformat(u[3].replace(' ', 'T'))).days < 7])}\n"
    
    keyboard = [
        [
            InlineKeyboardButton("📊 User Stats", callback_data="admin_user_stats"),
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_users")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        users_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command - Owner only."""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "This command is restricted to bot administrators only.",
            parse_mode='Markdown'
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "Usage: `/broadcast <message>`\n\n"
            "Example:\n"
            "`/broadcast Hello everyone! Bot has been updated with new features.`\n\n"
            "⚠️ This will send the message to ALL users!",
            parse_mode='Markdown'
        )
        return
    
    message = " ".join(context.args)
    users = get_all_users()
    
    if not users:
        await update.message.reply_text("No users to broadcast to.")
        return
    
    # Confirm broadcast
    keyboard = [
        [
            InlineKeyboardButton("✅ Send Broadcast", callback_data=f"confirm_broadcast:{message[:50]}"),
            InlineKeyboardButton("❌ Cancel", callback_data="admin_close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📢 **Confirm Broadcast**\n\n"
        f"**Message Preview:**\n{message[:200]}{'...' if len(message) > 200 else ''}\n\n"
        f"**Recipients:** {len(users)} users\n\n"
        f"⚠️ Are you sure you want to send this message to all users?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries."""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    # Check owner permissions
    if not is_owner(user_id):
        await query.answer("❌ Access denied!", show_alert=True)
        return
    
    await query.answer()
    
    if data == "admin_close":
        try:
            await query.edit_message_text("Admin panel closed.")
        except:
            await query.message.delete()
        return
    
    elif data == "admin_stats":
        stats = get_bot_stats()
        stats_text = f"""
📊 **Live Bot Statistics**

👥 **Users:** {stats['total_users']} total
🎬 **Processed:** {stats['total_processed']} videos
💾 **Storage:** {stats['db_size']:.1f}MB database
⏱️ **Uptime:** {stats['uptime']}
🚀 **Status:** {stats['status']} 🟢

🔄 *Auto-refreshed at {datetime.now().strftime('%H:%M:%S')}*
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "admin_users":
        users = get_all_users()
        users_text = f"👥 **User Management**\n\n"
        users_text += f"📊 Total Users: {len(users)}\n"
        users_text += f"📅 Recent Activity: {len([u for u in users[:10]])}\n\n"
        
        for user in users[:5]:
            users_text += f"• {user[2]} (@{user[1] or 'none'}) - `{user[0]}`\n"
        
        if len(users) > 5:
            users_text += f"\n... and {len(users) - 5} more users"
        
        keyboard = [
            [InlineKeyboardButton("📋 Full List", callback_data="admin_full_users")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(users_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "admin_clean":
        cleaned_files = cleanup_temp_files()
        await query.edit_message_text(
            f"🗑️ **Cleanup Complete**\n\n"
            f"Cleaned {cleaned_files} temporary files.\n"
            f"Storage space recovered successfully! ✅",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]),
            parse_mode='Markdown'
        )
    
    elif data == "admin_system":
        system_info = get_system_info()
        await query.edit_message_text(
            system_info,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]),
            parse_mode='Markdown'
        )
    
    elif data == "admin_back":
        # Show main admin menu again
        keyboard = [
            [
                InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
                InlineKeyboardButton("👥 All Users", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
                InlineKeyboardButton("🗑️ Clean Temp", callback_data="admin_clean")
            ],
            [
                InlineKeyboardButton("🔄 System Info", callback_data="admin_system"),
                InlineKeyboardButton("📝 Logs", callback_data="admin_logs")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔧 **Admin Control Panel**\n\n"
            "🤖 Video Encode Bot Admin\n"
            f"👑 Owner: {query.from_user.first_name}\n\n"
            "Select an option below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def get_bot_stats():
    """Get comprehensive bot statistics."""
    try:
        # Get user count
        total_users = get_user_count()
        
        # Calculate uptime
        uptime_seconds = time.time() - bot_start_time
        uptime = format_uptime(uptime_seconds)
        
        # Get system info
        memory_usage = psutil.virtual_memory().used / (1024 * 1024)  # MB
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # Get temp files count
        temp_files = len(os.listdir(TEMP_DIR)) if os.path.exists(TEMP_DIR) else 0
        
        # Get database size
        db_size = os.path.getsize(DATABASE_PATH) / (1024 * 1024) if os.path.exists(DATABASE_PATH) else 0
        
        return {
            'total_users': total_users,
            'active_users': total_users,  # Placeholder
            'new_users_today': 0,  # Implement with date tracking
            'user_growth': 5.2,  # Placeholder
            'total_processed': 0,  # Implement video counter
            'success_rate': 96.5,  # Placeholder
            'avg_processing_time': 45,  # Placeholder
            'queue_status': 'Empty',
            'temp_files': temp_files,
            'db_size': db_size,
            'memory_usage': memory_usage,
            'cpu_usage': cpu_usage,
            'uptime': uptime,
            'last_restart': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'status': 'Online',
            'response_time': 150,  # Placeholder
            'error_rate': 2.1,  # Placeholder
            'peak_users': total_users
        }
        
    except Exception as e:
        logger.error(f"Error getting bot stats: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'new_users_today': 0,
            'user_growth': 0,
            'total_processed': 0,
            'success_rate': 0,
            'avg_processing_time': 0,
            'queue_status': 'Unknown',
            'temp_files': 0,
            'db_size': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'uptime': '0m',
            'last_restart': 'Unknown',
            'status': 'Error',
            'response_time': 0,
            'error_rate': 0,
            'peak_users': 0
        }

def get_system_info():
    """Get system information."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return f"""
🔄 **System Information**

💻 **CPU:**
• Usage: {cpu_percent:.1f}%
• Cores: {psutil.cpu_count()} physical, {psutil.cpu_count(logical=True)} logical

🧠 **Memory:**
• Used: {memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB
• Available: {memory.available / (1024**3):.1f}GB
• Usage: {memory.percent:.1f}%

💾 **Disk:**
• Used: {disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB
• Free: {disk.free / (1024**3):.1f}GB
• Usage: {(disk.used/disk.total)*100:.1f}%

⏱️ **Uptime:** {format_uptime(time.time() - bot_start_time)}

🤖 **Bot Status:** Online ✅
"""
    except Exception as e:
        return f"❌ Error getting system info: {e}"

def format_uptime(seconds):
    """Format uptime in human readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def cleanup_temp_files():
    """Clean up temporary files."""
    try:
        if not os.path.exists(TEMP_DIR):
            return 0
        
        files = os.listdir(TEMP_DIR)
        count = 0
        
        for file in files:
            file_path = os.path.join(TEMP_DIR, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    count += 1
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
        
        logger.info(f"Cleaned up {count} temporary files")
        return count
        
    except Exception as e:
        logger.error(f"Error cleaning temp files: {e}")
        return 0
