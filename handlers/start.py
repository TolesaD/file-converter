from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from utils.keyboard_utils import get_main_menu_keyboard, get_format_suggestions_keyboard
import logging

logger = logging.getLogger(__name__)

async def is_user_banned(user_id):
    """Check if user is banned"""
    user = db.get_user_by_id(user_id)
    return user and user['is_banned']

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
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
    
    # Add user to database
    db.add_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = """
🤖 *Welcome to Professional File Converter Bot!*

I can automatically detect your file type and suggest the best conversion options!

📁 *Just upload any file and I'll show you what I can convert it to.*

✨ *Features:*
• Smart file type detection
• Automatic conversion suggestions  
• High quality conversions
• Support for large files (up to 2GB)

Try it now - upload any file! 🚀
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    user = update.effective_user
    
    help_text = """
📖 *File Converter Bot Help*

*How to use:*
1. Upload any file (image, audio, video, document)
2. I'll automatically detect the file type
3. Choose from suggested conversion options
4. Or browse all categories manually
5. Download your converted file

*Smart Detection Supports:*
*📷 Images:* PNG, JPG, JPEG, BMP, GIF, WEBP
*🔊 Audio:* MP3, WAV, AAC, OGG, FLAC  
*📹 Video:* MP4, AVI, MOV, MKV, WEBM
*💼 Documents:* PDF, DOCX, DOC, TXT, XLSX, XLS, ODT
*🖼 Presentations:* PPTX, PPT

*Tips:*
• Maximum file size: 2GB
• Files are automatically processed
• You can convert multiple files without restarting

Just upload a file to get started!
"""
    
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_menu_keyboard(user.id),
        parse_mode='Markdown'
    )

def detect_file_type(file_extension):
    """Detect file type from extension - IMPROVED DETECTION"""
    file_extension = file_extension.lower().lstrip('.')
    
    # Enhanced format mapping
    image_formats = ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp', 'tiff', 'tif', 'ico', 'svg']
    audio_formats = ['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a', 'wma', 'aiff']
    video_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v', '3gp']
    document_formats = ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'odt', 'rtf', 'csv', 'ppt', 'pptx', 'odp', 'ods']
    
    if file_extension in image_formats:
        return 'image', 'Image'
    elif file_extension in audio_formats:
        return 'audio', 'Audio'
    elif file_extension in video_formats:
        return 'video', 'Video'
    elif file_extension in document_formats:
        # Further categorize documents
        if file_extension in ['pdf']:
            return 'document', 'PDF Document'
        elif file_extension in ['docx', 'doc', 'odt', 'rtf']:
            return 'document', 'Word Document'
        elif file_extension in ['xlsx', 'xls', 'csv', 'ods']:
            return 'document', 'Spreadsheet'
        elif file_extension in ['ppt', 'pptx', 'odp']:
            return 'presentation', 'Presentation'
        else:
            return 'document', 'Document'
    else:
        return 'unknown', 'Unknown File'

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries - SIMPLIFIED AND FIXED"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    # Check if user is banned
    if await is_user_banned(user_id):
        await query.edit_message_text(
            "🚫 *Account Banned*\n\n"
            "Your account has been banned from using this bot. "
            "If you believe this is a mistake, please contact the administrator.",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"Callback from user {user_id}: {callback_data}")
    
    try:
        # Handle main menu navigation
        if callback_data == "main_menu":
            await show_main_menu(query)
            return
        
        # Handle upload now button
        elif callback_data == "upload_now":
            await query.edit_message_text(
                "📤 *Ready for Upload*\n\nPlease upload your file now. I'll automatically detect its type and show conversion options!",
                parse_mode='Markdown'
            )
            return
        
        # Handle conversion category selection
        elif callback_data == "convert_file":
            await query.edit_message_text(
                "📁 *Choose File Category*\n\nSelect the type of file you want to convert, or just upload any file for automatic detection:",
                reply_markup=get_conversion_categories_keyboard(),
                parse_mode='Markdown'
            )
            return
        
        # Handle specific category menus
        elif callback_data.startswith("menu_"):
            await handle_category_menu(query, callback_data)
            return
        
        # Handle conversion type selection
        elif callback_data.startswith("convert_"):
            await handle_conversion_selection(query, callback_data, context)
            return
        
        # Handle auto-convert from suggestions (SMART DETECTION)
        elif callback_data.startswith("auto_convert_"):
            await handle_auto_convert(query, callback_data, context)
            return
        
        # Handle history
        elif callback_data == "history":
            from handlers.history import show_history
            await show_history(update, context)
            return
        
        # Handle admin panel
        elif callback_data == "admin_panel":
            from handlers.admin import admin_panel
            await admin_panel(update, context)
            return
        
        # Default fallback - show main menu
        else:
            await show_main_menu(query)
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        await query.edit_message_text(
            "❌ Something went wrong. Please try again.",
            reply_markup=get_main_menu_keyboard(user_id)
        )

async def show_main_menu(query):
    """Show the main menu"""
    welcome_text = """
🤖 *Professional File Converter Bot*

I automatically detect file types and suggest conversion options!

💡 *How to use:*
1. Upload any file
2. I'll detect the type automatically  
3. Choose from smart suggestions
4. Get your converted file

Try it now - upload any file! 📁
"""
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(query.from_user.id),
        parse_mode='Markdown'
    )

def get_conversion_categories_keyboard():
    """Get keyboard for conversion categories"""
    keyboard = [
        [InlineKeyboardButton("📷 Convert Images", callback_data="menu_images")],
        [InlineKeyboardButton("🔊 Convert Audio", callback_data="menu_audio")],
        [InlineKeyboardButton("📹 Convert Video", callback_data="menu_video")],
        [InlineKeyboardButton("💼 Convert Documents", callback_data="menu_documents")],
        [InlineKeyboardButton("🖼 Convert Presentations", callback_data="menu_presentations")],
        [InlineKeyboardButton("📤 Or Upload Any File", callback_data="upload_now")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_category_menu(query, callback_data):
    """Handle category menu selection"""
    from utils.keyboard_utils import (
        get_image_conversion_keyboard, 
        get_audio_conversion_keyboard,
        get_video_conversion_keyboard,
        get_document_conversion_keyboard,
        get_presentation_conversion_keyboard
    )
    
    category_map = {
        "menu_images": ("📷 Image Conversion", get_image_conversion_keyboard),
        "menu_audio": ("🔊 Audio Conversion", get_audio_conversion_keyboard),
        "menu_video": ("📹 Video Conversion", get_video_conversion_keyboard),
        "menu_documents": ("💼 Document Conversion", get_document_conversion_keyboard),
        "menu_presentations": ("🖼 Presentation Conversion", get_presentation_conversion_keyboard)
    }
    
    if callback_data in category_map:
        title, keyboard_func = category_map[callback_data]
        await query.edit_message_text(
            f"{title}\n\nSelect the conversion type, or upload a file for automatic detection:",
            reply_markup=keyboard_func(),
            parse_mode='Markdown'
        )

async def handle_conversion_selection(query, callback_data, context):
    """Handle conversion type selection"""
    try:
        # Parse conversion type from callback data
        # Format: convert_{category}_{input}_{output}
        parts = callback_data.split('_')
        
        if len(parts) >= 4:
            category = parts[1]  # img, audio, video, doc, presentation
            input_format = parts[2]  # png, jpg, pdf, etc.
            output_format = parts[3]  # jpg, png, pdf, etc.
            
            # Map category to full name for display
            category_names = {
                'img': 'Image',
                'audio': 'Audio', 
                'video': 'Video',
                'doc': 'Document',
                'presentation': 'Presentation'
            }
            
            category_name = category_names.get(category, 'File')
            
            # Store conversion info in context
            context.user_data['conversion_type'] = f"{input_format}_to_{output_format}"
            context.user_data['output_format'] = output_format
            context.user_data['file_type'] = category
            context.user_data['expecting_followup_upload'] = True

            # Show upload prompt
            upload_text = f"""
🎯 *{category_name} Conversion Selected*

🔄 Conversion: `{input_format.upper()}` → `{output_format.upper()}`

📤 Please upload your `{input_format.upper()}` file now.

I'll process it and show you the converted file!
"""
            
            keyboard = [
                [InlineKeyboardButton("📤 Upload File Now", callback_data="upload_now")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
            
            await query.edit_message_text(
                upload_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        else:
            raise ValueError("Invalid callback data format")
            
    except Exception as e:
        logger.error(f"Error handling conversion selection: {e}")
        await query.edit_message_text(
            "❌ Error processing your selection. Please try again.",
            reply_markup=get_main_menu_keyboard(query.from_user.id)
        )

async def handle_auto_convert(query, callback_data, context):
    """Handle auto-convert from smart suggestions - FIXED"""
    try:
        # Format: auto_convert_{input}_{output}
        parts = callback_data.split('_')
        
        if len(parts) >= 4:
            input_format = parts[2]
            output_format = parts[3]
            
            # Detect category from input format
            file_type, category_name = detect_file_type(input_format)
            
            # Store conversion info in context
            context.user_data['conversion_type'] = f"{input_format}_to_{output_format}"
            context.user_data['output_format'] = output_format
            context.user_data['file_type'] = file_type
            context.user_data['expecting_followup_upload'] = True

            # Show upload prompt
            upload_text = f"""
🎯 *Smart Conversion Selected*

🔄 Conversion: `{input_format.upper()}` → `{output_format.upper()}`
📁 Type: {category_name}

📤 Please upload your `{input_format.upper()}` file now.

I'll automatically convert it for you!
"""
            
            keyboard = [
                [InlineKeyboardButton("📤 Upload File Now", callback_data="upload_now")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
            
            await query.edit_message_text(
                upload_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error handling auto convert: {e}")
        await query.edit_message_text(
            "❌ Error processing conversion. Please try again.",
            reply_markup=get_main_menu_keyboard(query.from_user.id)
        )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user conversion history"""
    from handlers.history import show_history as show_user_history
    await show_user_history(update, context)