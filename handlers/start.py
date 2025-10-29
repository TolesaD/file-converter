from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import Config
from utils.keyboard_utils import (
    get_main_menu_keyboard, 
    get_commands_keyboard,
    get_document_conversion_keyboard,
    get_image_conversion_keyboard,
    get_audio_conversion_keyboard,
    get_video_conversion_keyboard,
    get_presentation_conversion_keyboard,
    get_format_suggestions_keyboard,
    get_admin_keyboard
)
import logging
import os

logger = logging.getLogger(__name__)

async def is_user_banned(user_id):
    """Check if user is banned"""
    user = db.get_user_by_id(user_id)
    return user and user['is_banned']

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu"""
    user = update.effective_user
    user_id = user.id
    
    # Check if user is banned
    if await is_user_banned(user_id):
        await update.message.reply_text(
            "🚫 *Account Banned*\n\n"
            "Your account has been banned from using this bot. "
            "If you believe this is a mistake, please contact the administrator.",
            parse_mode='Markdown'
        )
        return
    
    # Clear any existing context data
    context.user_data.clear()
    
    # Add user to database
    db.add_user(user_id, user.username, user.first_name, user.last_name)
    
    welcome_text = f"""
👋 Welcome *{user.first_name}* to the *World-Class File Converter Bot*! 🚀

*Professional Features:*
• 🎯 High-quality professional conversions
• 🧠 Smart file type detection  
• ⚡ Fast multi-format support
• 📊 Real-time progress updates
• 🏆 Professional-grade output quality

*Supported Categories:*
📷 Images: PNG, JPG, JPEG, BMP, GIF (20+ professional conversions)
🔊 Audio: MP3, WAV, AAC (6 high-quality conversions)
📹 Video: MP4, AVI, MOV, MKV (12 professional conversions)
💼 Documents: PDF, DOCX, TXT, XLSX, ODT (12 accurate conversions)
🖼 Presentations: PPTX, PPT (3 professional conversions)

*Total: 53+ professional-grade conversions!*

*Simply upload any file for automatic professional conversion!*
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help information"""
    user_id = update.effective_user.id
    
    # Check if user is banned
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 Your account has been banned.")
        return
    
    is_admin = user_id in Config.ADMIN_IDS
    
    help_text = """
🤖 *How to use this bot:*

1. *Upload any file* - I'll automatically detect its type
2. *Choose from suggestions* - See all possible conversions
3. *Or use menus* - Browse specific conversion types
4. *Wait for processing* - Real-time progress updates
5. *Download result* - Get your converted file

📁 *Smart Detection Supported:*
• Upload any file → Get automatic conversion suggestions
• Or use category menus for specific conversions

⚡ *Tips:*
• Max file size: 50MB
• Multiple files processed simultaneously
• Conversion history saved
• Queue system for fair processing

🔧 *Available Commands:*
• /start - Start bot
• /help - This help
• /history - Your conversions
"""
    
    # Only show admin commands to admins
    if is_admin:
        help_text += "• /stats - System stats (admin)\n• /admin - Admin panel (admin)"
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user history - accessible to all users"""
    user_id = update.effective_user.id
    
    # Check if user is banned
    if await is_user_banned(user_id):
        await update.message.reply_text("🚫 Your account has been banned.")
        return
    
    from handlers.history import show_history as show_user_history
    await show_user_history(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    # Check if user is banned (except for admin callbacks)
    admin_callbacks = ["admin_stats", "admin_stats_live", "admin_stats_daily", 
                      "admin_stats_users", "admin_stats_formats", "admin_users",
                      "admin_broadcast", "admin_reports", "admin_refresh", "admin_panel",
                      "admin_view_users", "admin_banned_users", "broadcast_confirm",
                      "admin_view_user_", "admin_ban_user_", "admin_unban_user_", "admin_back_to_users"]
    
    is_admin_callback = any(callback_data.startswith(cb) for cb in admin_callbacks) or callback_data in admin_callbacks
    
    if not is_admin_callback and await is_user_banned(user_id):
        await query.edit_message_text(
            "🚫 *Account Banned*\n\n"
            "Your account has been banned from using this bot. "
            "If you believe this is a mistake, please contact the administrator.",
            parse_mode='Markdown'
        )
        return
    
    is_admin = user_id in Config.ADMIN_IDS
    
    logger.info(f"Callback received: {callback_data} from user {user_id}")
    
    # Handle admin-only callbacks
    if is_admin_callback:
        if not is_admin:
            await query.edit_message_text("❌ Access denied. Admin only.")
            return
        # Route to admin handler
        from handlers.admin import handle_admin_callback
        await handle_admin_callback(update, context)
        return
    
    # Rest of callback handling
    if callback_data == "main_menu":
        await show_main_menu(query, user_id)
    elif callback_data == "commands":
        await show_commands_menu(query, user_id)
    elif callback_data == "menu_documents":
        await show_document_menu(query)
    elif callback_data == "menu_images":
        await show_image_menu(query)
    elif callback_data == "menu_audio":
        await show_audio_menu(query)
    elif callback_data == "menu_video":
        await show_video_menu(query)
    elif callback_data == "menu_presentations":
        await show_presentation_menu(query)
    elif callback_data.startswith("convert_doc_"):
        parts = callback_data.replace("convert_doc_", "").split("_")
        if len(parts) == 2:
            await start_auto_conversion(query, context, parts[0], parts[1], 'document')
    elif callback_data.startswith("convert_img_"):
        parts = callback_data.replace("convert_img_", "").split("_")
        if len(parts) == 2:
            await start_auto_conversion(query, context, parts[0], parts[1], 'image')
    elif callback_data.startswith("convert_audio_"):
        parts = callback_data.replace("convert_audio_", "").split("_")
        if len(parts) == 2:
            await start_auto_conversion(query, context, parts[0], parts[1], 'audio')
    elif callback_data.startswith("convert_video_"):
        parts = callback_data.replace("convert_video_", "").split("_")
        if len(parts) == 2:
            await start_auto_conversion(query, context, parts[0], parts[1], 'video')
    elif callback_data.startswith("convert_presentation_"):
        parts = callback_data.replace("convert_presentation_", "").split("_")
        if len(parts) == 2:
            await start_auto_conversion(query, context, parts[0], parts[1], 'presentation')
    elif callback_data.startswith("auto_convert_"):
        # Handle smart conversion suggestions from direct uploads
        parts = callback_data.replace("auto_convert_", "").split("_")
        if len(parts) == 2:
            source_format, target_format = parts
            file_type, _ = detect_file_type(source_format)
            await start_auto_conversion(query, context, source_format, target_format, file_type)
    elif callback_data == "admin_panel":
        await show_admin_panel(query, user_id)
    elif callback_data == "history":
        from handlers.history import handle_history_callback
        await handle_history_callback(update, context)
    elif callback_data == "convert_file":
        # This is the main convert file button - show upload prompt
        await query.edit_message_text(
            "📁 *File Upload*\n\nPlease upload any file you want to convert.\n\n"
            "I'll automatically detect the file type and show you all available conversion options!",
            parse_mode='Markdown'
        )
    elif callback_data == "browse_formats":
        await show_commands_menu(query, user_id)
    elif callback_data == "none":
        pass
    else:
        logger.warning(f"Unhandled callback: {callback_data}")

async def show_main_menu(query, user_id):
    """Show main menu with simplified categories"""
    menu_text = """
🏠 *Main Menu*

Choose a category to convert files:

📷 *Images* - PNG, JPG, JPEG, BMP, GIF (20+ conversions)
🔊 *Audio* - MP3, WAV, AAC (6 conversions)  
📹 *Video* - MP4, AVI, MOV, MKV (12 conversions)
💼 *Documents* - PDF, DOCX, TXT, XLSX, ODT (12 conversions)
🖼 *Presentations* - PPTX, PPT (3 conversions)

*Total: 53+ reliable conversions!*

*Or simply upload any file for automatic detection!*
"""
    
    await query.edit_message_text(
        menu_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )

async def show_commands_menu(query, user_id):
    commands_text = "📋 *Available Commands*\n\nUse these commands in the chat:"
    
    # For admins, show admin commands in the text
    if user_id in Config.ADMIN_IDS:
        commands_text += "\n\n👑 *Admin Commands:*\n• /stats - System statistics\n• /admin - Admin panel"
    
    await query.edit_message_text(
        commands_text,
        reply_markup=get_commands_keyboard(),
        parse_mode='Markdown'
    )

async def show_document_menu(query):
    """Show document conversion menu"""
    await query.edit_message_text(
        "💼 *Document Conversion*\n\nSupported formats: PDF, DOCX, TXT, XLSX, ODT\n\nChoose conversion type:",
        reply_markup=get_document_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_image_menu(query):
    """Show image conversion menu"""
    await query.edit_message_text(
        "📷 *Image Conversion*\n\nSupported formats: PNG, JPG, JPEG, BMP, GIF\n\nChoose conversion type:",
        reply_markup=get_image_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_audio_menu(query):
    """Show audio conversion menu"""
    await query.edit_message_text(
        "🔊 *Audio Conversion*\n\nSupported formats: MP3, WAV, AAC\n\nChoose conversion type:",
        reply_markup=get_audio_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_video_menu(query):
    """Show video conversion menu"""
    await query.edit_message_text(
        "📹 *Video Conversion*\n\nSupported formats: MP4, AVI, MOV, MKV\n\nChoose conversion type:",
        reply_markup=get_video_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_presentation_menu(query):
    """Show presentation conversion menu"""
    await query.edit_message_text(
        "🖼 *Presentation Conversion*\n\nSupported formats: PPTX, PPT\n\nChoose conversion type:",
        reply_markup=get_presentation_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_admin_panel(query, user_id):
    """Show admin panel only for admins"""
    if user_id not in Config.ADMIN_IDS:
        await query.edit_message_text("❌ Access denied. Admin only.")
        return
    
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

async def start_auto_conversion(query, context, source_format, target_format, file_type=None):
    """Start conversion from auto-detected file type"""
    if not file_type:
        file_type, _ = detect_file_type(source_format)
    
    # Store conversion details in context
    context.user_data['conversion_type'] = f"auto_{source_format}_{target_format}"
    context.user_data['input_format'] = source_format
    context.user_data['output_format'] = target_format
    context.user_data['file_type'] = file_type
    
    logger.info(f"Starting auto conversion: {source_format} -> {target_format} (file_type: {file_type})")
    
    # Check if we already have a downloaded file from smart detection
    if 'detected_file_info' in context.user_data:
        file_info = context.user_data['detected_file_info']
        
        # Verify the file still exists and matches the selected format
        if os.path.exists(file_info['path']) and file_info['extension'].lower() == source_format.lower():
            # We have a file ready to process!
            message_text = f"""
✅ *Smart Conversion Ready!*

📁 File: `{file_info['name']}`
🔍 Type: {source_format.upper()} ({Config.FORMAT_CATEGORIES.get(file_type, '📁 File')})
🎯 Target: {target_format.upper()}

🔄 Starting conversion now...
"""
            
            await query.edit_message_text(message_text, parse_mode='Markdown')
            
            # Import the conversion handler
            from handlers.conversion import process_file_directly
            
            # Process the file immediately
            try:
                await process_file_directly(query, context, file_info['path'], source_format, query.from_user.id)
                
                # Clear the detected file info after successful processing
                context.user_data.pop('detected_file_info', None)
                
            except Exception as e:
                logger.error(f"Error in immediate processing: {e}")
                await query.edit_message_text(f"❌ Error starting conversion: {str(e)}")
        else:
            # File doesn't exist or format doesn't match, ask for re-upload
            context.user_data['expecting_followup_upload'] = True
            message_text = f"""
🧠 *Conversion Type Selected*

📁 File Type: {source_format.upper()} 
🎯 Target Format: {target_format.upper()}

Please upload your {source_format.upper()} file to start conversion.
"""
            await query.edit_message_text(message_text, parse_mode='Markdown')
            
            # Clean up old file if it exists but doesn't match
            if 'detected_file_info' in context.user_data:
                old_file_info = context.user_data.pop('detected_file_info')
                if os.path.exists(old_file_info['path']):
                    try:
                        os.remove(old_file_info['path'])
                    except:
                        pass
    else:
        # No file available, ask user to upload
        context.user_data['expecting_followup_upload'] = True
        message_text = f"""
🧠 *Conversion Type Selected*

📁 File Type: {source_format.upper()} ({Config.FORMAT_CATEGORIES.get(file_type, '📁 File')})
🎯 Target Format: {target_format.upper()}

Please upload your {source_format.upper()} file to start conversion.
"""
        
        await query.edit_message_text(message_text, parse_mode='Markdown')

def detect_file_type(file_extension):
    """Detect file type category using simplified format list"""
    file_extension = file_extension.lower()
    
    for file_type, extensions in Config.SUPPORTED_FORMATS.items():
        if file_extension in extensions:
            return file_type, Config.FORMAT_CATEGORIES[file_type]
    
    return 'unknown', '📁 Unknown'