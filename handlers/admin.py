from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from config import Config
from utils.keyboard_utils import get_admin_keyboard, get_main_menu_keyboard, get_admin_stats_keyboard, get_cancel_keyboard
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel access"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    admin_text = """
👑 *Admin Panel*

*Quick Actions:*
• View real-time system statistics
• Manage users and monitor activity  
• Send broadcast messages
• Generate detailed reports

Use the buttons below or commands:
• /stats - System statistics
• /admin - This panel
    """
    
    await update.message.reply_text(
        admin_text,
        reply_markup=get_admin_keyboard(),
        parse_mode='Markdown'
    )

async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system statistics"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text("❌ Access denied. Admin only.")
        else:
            await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    stats_text = await get_live_system_stats()
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            stats_text, 
            reply_markup=get_admin_stats_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            stats_text,
            reply_markup=get_admin_stats_keyboard(),
            parse_mode='Markdown'
        )

async def get_live_system_stats():
    """Get live system statistics"""
    stats = db.get_system_stats()
    
    # Get additional stats
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Today's conversions
    cursor.execute('''
        SELECT COUNT(*) FROM conversion_jobs 
        WHERE DATE(created_at) = DATE('now')
    ''')
    today_conversions = cursor.fetchone()[0]
    
    # Active users (last 7 days)
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM conversion_jobs 
        WHERE created_at >= datetime('now', '-7 days')
    ''')
    active_users_7d = cursor.fetchone()[0]
    
    # Format usage
    cursor.execute('''
        SELECT input_type, COUNT(*) as count 
        FROM history 
        WHERE success = 1 
        GROUP BY input_type 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    top_formats = cursor.fetchall()
    
    conn.close()
    
    stats_text = f"""
📊 *System Statistics - Live Dashboard*

👥 *Users:*
• Total Users: `{stats['total_users']}`
• Active (7 days): `{active_users_7d}`
• Banned Users: `{len(db.get_banned_users())}`

🔄 *Conversions:*
• Total: `{stats['total_conversions']}`
• Successful: `{stats['successful_conversions']}`
• Today: `{today_conversions}`
• Success Rate: `{(stats['successful_conversions'] / stats['total_conversions'] * 100) if stats['total_conversions'] > 0 else 0:.1f}%`

📈 *Queue Status:*
• Active Jobs: `{Config.active_jobs}`
• Queued Jobs: `{db.get_queued_jobs_count()}`
• Max Concurrent: `{Config.MAX_CONCURRENT_JOBS}`

🏆 *Top Formats:*
"""
    
    for fmt, count in top_formats:
        stats_text += f"• `{fmt.upper()}`: {count} conversions\n"
    
    stats_text += f"\n🕒 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return stats_text

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in Config.ADMIN_IDS:
        await query.edit_message_text("❌ Access denied. Admin only.")
        return
    
    callback_data = query.data
    
    if callback_data == "admin_stats":
        await show_admin_stats_from_query(query, context)
    elif callback_data == "admin_stats_live":
        await show_admin_stats_from_query(query, context)
    elif callback_data == "admin_stats_daily":
        await show_daily_report(query)
    elif callback_data == "admin_stats_users":
        await show_user_analytics(query)
    elif callback_data == "admin_stats_formats":
        await show_format_usage(query)
    elif callback_data == "admin_users":
        await show_user_management(query)
    elif callback_data == "admin_broadcast":
        await start_broadcast(query, context)
    elif callback_data == "admin_reports":
        await show_reports(query)
    elif callback_data == "admin_refresh":
        await show_admin_stats_from_query(query, context)
    elif callback_data == "admin_panel":
        await show_admin_panel(query)
    elif callback_data == "main_menu":
        await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    elif callback_data == "broadcast_confirm":
        await confirm_broadcast(query, context)
    elif callback_data == "admin_view_users":
        await show_all_users(query)
    elif callback_data == "admin_banned_users":
        await show_banned_users(query)
    elif callback_data.startswith("admin_view_user_"):
        user_id_to_view = int(callback_data.replace("admin_view_user_", ""))
        await view_user_details(query, user_id_to_view)
    elif callback_data.startswith("admin_ban_user_"):
        user_id_to_ban = int(callback_data.replace("admin_ban_user_", ""))
        await ban_user(query, user_id_to_ban)
    elif callback_data.startswith("admin_unban_user_"):
        user_id_to_unban = int(callback_data.replace("admin_unban_user_", ""))
        await unban_user(query, user_id_to_unban)
    elif callback_data == "admin_back_to_users":
        await show_user_management(query)

async def show_admin_stats_from_query(query, context):
    """Show admin stats from callback query"""
    stats_text = await get_live_system_stats()
    await query.edit_message_text(
        stats_text,
        reply_markup=get_admin_stats_keyboard(),
        parse_mode='Markdown'
    )

async def show_admin_panel(query):
    """Show admin panel"""
    admin_text = """
👑 *Admin Panel*

*Quick Actions:*
• View real-time system statistics
• Manage users and monitor activity
• Send broadcast messages
• Generate detailed reports

Use the buttons below to manage the system:
    """
    
    await query.edit_message_text(
        admin_text,
        reply_markup=get_admin_keyboard(),
        parse_mode='Markdown'
    )

async def show_daily_report(query):
    """Show daily conversion report"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Today's stats
    cursor.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM conversion_jobs 
        WHERE DATE(created_at) = DATE('now')
    ''')
    today_stats = cursor.fetchone()
    
    # Format distribution today
    cursor.execute('''
        SELECT input_type, COUNT(*) as count 
        FROM conversion_jobs 
        WHERE DATE(created_at) = DATE('now')
        GROUP BY input_type 
        ORDER BY count DESC
    ''')
    today_formats = cursor.fetchall()
    
    conn.close()
    
    report_text = f"""
📈 *Daily Report - {datetime.now().strftime("%Y-%m-%d")}*

📊 *Today's Summary:*
• Total Conversions: `{today_stats[0] or 0}`
• Successful: `{today_stats[1] or 0}`
• Failed: `{today_stats[2] or 0}`
• Success Rate: `{(today_stats[1] / today_stats[0] * 100) if today_stats[0] and today_stats[0] > 0 else 0:.1f}%`

📁 *Format Distribution Today:*
"""
    
    for fmt, count in today_formats[:8]:
        report_text += f"• `{fmt.upper()}`: {count}\n"
    
    if not today_formats:
        report_text += "• No conversions today\n"
    
    report_text += f"\n🕒 Generated: {datetime.now().strftime('%H:%M:%S')}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats_daily"),
         InlineKeyboardButton("📊 Main Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]
    ]
    
    await query.edit_message_text(
        report_text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_user_analytics(query):
    """Show user analytics"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Top users by conversions
    cursor.execute('''
        SELECT u.username, u.first_name, u.total_conversions 
        FROM users u 
        ORDER BY u.total_conversions DESC 
        LIMIT 10
    ''')
    top_users = cursor.fetchall()
    
    conn.close()
    
    analytics_text = """
👥 *User Analytics*

🏆 *Top Users (by conversions):*
"""
    
    for i, (username, first_name, conversions) in enumerate(top_users, 1):
        display_name = f"@{username}" if username else first_name
        analytics_text += f"{i}. `{display_name}`: {conversions} conversions\n"
    
    if not top_users:
        analytics_text += "• No users yet\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats_users"),
         InlineKeyboardButton("📊 Main Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]
    ]
    
    await query.edit_message_text(
        analytics_text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_format_usage(query):
    """Show format usage statistics"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Most popular conversions
    cursor.execute('''
        SELECT input_type, output_type, COUNT(*) as count
        FROM history 
        WHERE success = 1
        GROUP BY input_type, output_type 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    popular_conversions = cursor.fetchall()
    
    conn.close()
    
    format_text = """
📁 *Format Usage Statistics*

🔥 *Most Popular Conversions:*
"""
    
    for i, (input_fmt, output_fmt, count) in enumerate(popular_conversions, 1):
        format_text += f"{i}. `{input_fmt.upper()}→{output_fmt.upper()}`: {count}\n"
    
    if not popular_conversions:
        format_text += "• No conversions yet\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats_formats"),
         InlineKeyboardButton("📊 Main Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]
    ]
    
    await query.edit_message_text(
        format_text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_user_management(query):
    """Show user management interface"""
    all_users = db.get_all_users()
    banned_users = db.get_banned_users()
    
    user_text = f"""
👥 *User Management*

📊 *Quick Stats:*
• Total Users: `{len(all_users)}`
• Banned Users: `{len(banned_users)}`
• Active Users: `{len(all_users) - len(banned_users)}`

🔨 *User Actions:*
• View all users with ban options
• Manage banned users
• User statistics
• Export user data

*Use the buttons below to manage users:*
    """
    
    keyboard = [
        [InlineKeyboardButton("👤 View All Users", callback_data="admin_view_users"),
         InlineKeyboardButton("🚫 Banned Users", callback_data="admin_banned_users")],
        [InlineKeyboardButton("📧 Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton("📊 User Stats", callback_data="admin_stats_users")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]
    ]
    
    await query.edit_message_text(
        user_text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_all_users(query):
    """Show all users with ban/unban options"""
    users = db.get_all_users()
    
    if not users:
        users_text = "👤 *No Users Found*"
        keyboard = [[InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")]]
    else:
        users_text = "👤 *All Users*\n\n"
        
        for i, user in enumerate(users[:15], 1):  # Show first 15 users
            status = "🚫" if user['is_banned'] else "✅"
            username = f"@{user['username']}" if user['username'] else user['first_name']
            users_text += f"{i}. {status} `{username}` (ID: {user['user_id']}) - {user['total_conversions']} conversions\n"
        
        if len(users) > 15:
            users_text += f"\n... and {len(users) - 15} more users"
        
        keyboard = [
            [InlineKeyboardButton("🚫 Banned Users", callback_data="admin_banned_users")],
            [InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")]
        ]
    
    await query.edit_message_text(
        users_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_banned_users(query):
    """Show banned users with unban options"""
    banned_users = db.get_banned_users()
    
    if not banned_users:
        banned_text = "🚫 *No Banned Users*"
        keyboard = [[InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")]]
    else:
        banned_text = "🚫 *Banned Users*\n\n"
        
        for i, user in enumerate(banned_users, 1):
            username = f"@{user['username']}" if user['username'] else user['first_name']
            banned_text += f"{i}. `{username}` (ID: {user['user_id']})\n"
        
        keyboard = [
            [InlineKeyboardButton("👤 View All Users", callback_data="admin_view_users")],
            [InlineKeyboardButton("🔙 Back to User Management", callback_data="admin_users")]
        ]
    
    await query.edit_message_text(
        banned_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def view_user_details(query, user_id):
    """Show detailed user information with ban/unban options"""
    user = db.get_user_by_id(user_id)
    
    if not user:
        await query.edit_message_text("❌ User not found.")
        return
    
    status = "🚫 Banned" if user['is_banned'] else "✅ Active"
    username = f"@{user['username']}" if user['username'] else "Not set"
    
    user_details = f"""
👤 *User Details*

*Basic Information:*
• User ID: `{user['user_id']}`
• Username: `{username}`
• First Name: `{user['first_name']}`
• Last Name: `{user['last_name'] or 'Not set'}`
• Status: {status}

*Statistics:*
• Total Conversions: `{user['total_conversions']}`
• Account Created: `{user.get('registration_date', 'Unknown')}`

*Actions:*
    """
    
    keyboard_buttons = []
    if user['is_banned']:
        keyboard_buttons.append(InlineKeyboardButton("✅ Unban User", callback_data=f"admin_unban_user_{user_id}"))
    else:
        keyboard_buttons.append(InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_user_{user_id}"))
    
    keyboard = [
        keyboard_buttons,
        [InlineKeyboardButton("🔙 Back to Users", callback_data="admin_users")]
    ]
    
    await query.edit_message_text(
        user_details,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ban_user(query, user_id):
    """Ban a user"""
    user = db.get_user_by_id(user_id)
    
    if not user:
        await query.edit_message_text("❌ User not found.")
        return
    
    if user['is_banned']:
        await query.edit_message_text("⚠️ User is already banned.")
        return
    
    success = db.ban_user(user_id)
    
    if success:
        username = f"@{user['username']}" if user['username'] else user['first_name']
        await query.edit_message_text(
            f"✅ Successfully banned user: `{username}` (ID: {user_id})",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Users", callback_data="admin_users")]]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ Failed to ban user.")

async def unban_user(query, user_id):
    """Unban a user"""
    user = db.get_user_by_id(user_id)
    
    if not user:
        await query.edit_message_text("❌ User not found.")
        return
    
    if not user['is_banned']:
        await query.edit_message_text("⚠️ User is not banned.")
        return
    
    success = db.unban_user(user_id)
    
    if success:
        username = f"@{user['username']}" if user['username'] else user['first_name']
        await query.edit_message_text(
            f"✅ Successfully unbanned user: `{username}` (ID: {user_id})",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Users", callback_data="admin_users")]]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ Failed to unban user.")

async def start_broadcast(query, context):
    """Start broadcast message process"""
    context.user_data['awaiting_broadcast'] = True
    context.user_data['broadcast_step'] = 'message'
    
    broadcast_text = """
📢 *Broadcast Message*

You can send a message to all registered users.

*Steps:*
1. Send me the broadcast message
2. I'll show you a preview
3. Confirm to send to all users

*Available formatting:*
• Markdown formatting
• Emojis supported
• Links work normally

Please send your broadcast message now, or use /cancel to abort.
    """
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]]
    
    await query.edit_message_text(
        broadcast_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming broadcast message"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if not context.user_data.get('awaiting_broadcast'):
        return
    
    if context.user_data.get('broadcast_step') == 'message':
        broadcast_text = update.message.text
        context.user_data['broadcast_text'] = broadcast_text
        
        # Get user count for confirmation
        users = db.get_all_users()
        user_count = len([u for u in users if not u['is_banned']])  # Only active users
        
        confirm_text = f"""
📢 *Broadcast Preview*

*Message:*
{broadcast_text}

*Recipients:* {user_count} active users

*Are you sure you want to send this broadcast?*
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Send Broadcast", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("✏️ Edit Message", callback_data="admin_broadcast"),
             InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]
        ]
        
        await update.message.reply_text(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        context.user_data['broadcast_step'] = 'confirm'

async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and send broadcast - FIXED VERSION"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in Config.ADMIN_IDS:
        await query.edit_message_text("❌ Access denied. Admin only.")
        return
    
    broadcast_text = context.user_data.get('broadcast_text', '')
    
    if not broadcast_text:
        await query.edit_message_text("❌ No broadcast message found.")
        return
    
    # Get all active users (not banned)
    users = db.get_all_users()
    active_users = [u for u in users if not u['is_banned']]
    total_users = len(active_users)
    
    if total_users == 0:
        await query.edit_message_text("❌ No active users to send broadcast to.")
        return
    
    successful_sends = 0
    failed_sends = 0
    
    # Send to all active users
    progress_msg = await query.edit_message_text(f"📤 Sending broadcast to {total_users} users...\n\nProgress: 0/{total_users}")
    
    from telegram import Bot
    bot = Bot(Config.BOT_TOKEN)
    
    for i, user in enumerate(active_users, 1):
        try:
            await bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 *Broadcast Message*\n\n{broadcast_text}",
                parse_mode='Markdown'
            )
            successful_sends += 1
        except Exception as e:
            failed_sends += 1
            logger.error(f"Failed to send broadcast to user {user['user_id']}: {e}")
        
        # Update progress every 10 users or at the end
        if i % 10 == 0 or i == total_users:
            try:
                await progress_msg.edit_text(
                    f"📤 Sending broadcast to {total_users} users...\n\n"
                    f"Progress: {i}/{total_users}\n"
                    f"✅ Successful: {successful_sends}\n"
                    f"❌ Failed: {failed_sends}"
                )
            except:
                pass  # Ignore message not modified errors
    
    # Final result
    result_text = f"""
✅ *Broadcast Completed*

*Results:*
• Total Users: {total_users}
• ✅ Successful: {successful_sends}
• ❌ Failed: {failed_sends}
• 📊 Success Rate: {(successful_sends/total_users*100) if total_users > 0 else 0:.1f}%

*Message sent to all active users successfully!*
    """
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
    
    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    # Cleanup
    context.user_data.pop('awaiting_broadcast', None)
    context.user_data.pop('broadcast_step', None)
    context.user_data.pop('broadcast_text', None)

async def show_reports(query):
    """Show admin reports"""
    reports_text = """
📈 *Admin Reports*

*Available Reports:*
• 📊 Real-time statistics
• 📅 Daily conversion reports  
• 👥 User activity analytics
• 📁 Format usage statistics

*Export Options:*
• User data export
• Conversion history logs

Use the statistics buttons for detailed analytics.
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 Live Stats", callback_data="admin_stats"),
         InlineKeyboardButton("📅 Daily Report", callback_data="admin_stats_daily")],
        [InlineKeyboardButton("👥 User Analytics", callback_data="admin_stats_users"),
         InlineKeyboardButton("📁 Format Usage", callback_data="admin_stats_formats")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]
    ]
    
    await query.edit_message_text(
        reports_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )