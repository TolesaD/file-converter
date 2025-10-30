from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from utils.keyboard_utils import get_main_menu_keyboard
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

I can convert your files between various formats with high quality and accuracy.

📁 *Supported Conversions:*
• 📷 Images (PNG, JPG, JPEG, BMP, GIF)
• 🔊 Audio (MP3, WAV, AAC)  
• 📹 Video (MP4, AVI, MOV, MKV)
• 💼 Documents (PDF, DOCX, TXT, XLSX, ODT)
• 🖼 Presentations (PPTX, PPT)

✨ *Features:*
• High quality conversions
• Fast processing
• Support for large files
• Multiple format options

Use the buttons below to get started! 🚀
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
1. Click *"Convert File"* or choose a specific category
2. Select the conversion type you want
3. Upload your file when prompted
4. Wait for processing
5. Download your converted file

*Supported Formats:*

*📷 Images:* PNG, JPG, JPEG, BMP, GIF
*🔊 Audio:* MP3, WAV, AAC
*📹 Video:* MP4, AVI, MOV, MKV  
*💼 Documents:* PDF, DOCX, TXT, XLSX, ODT
*🖼 Presentations:* PPTX, PPT

*Tips:*
• Files are automatically deleted after 24 hours
• Maximum file size: 2GB
• Conversion time depends on file size and type

Need help? Contact the administrator.
"""
    
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_menu_keyboard(user.id),
        parse_mode='Markdown'
    )

def detect_file_type(file_extension):
    """Detect file type from extension"""
    file_extension = file_extension.lower().lstrip('.')
    
    # Map extensions to categories
    image_formats = ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp']
    audio_formats = ['mp3', 'wav', 'aac', 'ogg', 'flac']
    video_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv']
    document_formats = ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'odt', 'rtf']
    presentation_formats = ['pptx', 'ppt', 'odp']
    
    if file_extension in image_formats:
        return 'image', 'Image'
    elif file_extension in audio_formats:
        return 'audio', 'Audio'
    elif file_extension in video_formats:
        # Special handling for GIF - it should be treated as image, not video
        if file_extension == 'gif':
            return 'image', 'Image (GIF)'
        return 'video', 'Video'
    elif file_extension in document_formats:
        return 'document', 'Document'
    elif file_extension in presentation_formats:
        return 'presentation', 'Presentation'
    else:
        return 'unknown', 'Unknown'

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
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
    
    # Handle main menu navigation
    if callback_data == "main_menu":
        await show_main_menu(query)
        return
    
    # Handle conversion category selection
    elif callback_data == "convert_file":
        await query.edit_message_text(
            "📁 *Choose File Category*\n\nSelect the type of file you want to convert:",
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
    
    # Handle auto-convert from suggestions
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
    
    # Default fallback
    else:
        await query.edit_message_text(
            "❌ Unknown command. Please use the menu below:",
            reply_markup=get_main_menu_keyboard(user_id)
        )

async def show_main_menu(query):
    """Show the main menu"""
    welcome_text = """
🤖 *Professional File Converter Bot*

Choose an option below to get started with file conversion:
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
            f"{title}\n\nSelect the conversion type:",
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
            
            # Show upload prompt with CONTINUE menu
            upload_text = f"""
🎯 *{category_name} Conversion Selected*

🔄 Conversion: `{input_format.upper()}` → `{output_format.upper()}`

📤 Please upload your `{input_format.upper()}` file now.

After conversion, you'll be able to convert another file without restarting!
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
    """Handle auto-convert from smart suggestions"""
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
            
            # Show upload prompt
            upload_text = f"""
🎯 *Smart Conversion Selected*

🔄 Conversion: `{input_format.upper()}` → `{output_format.upper()}`
📁 Type: {category_name}

📤 Please upload your `{input_format.upper()}` file now.

After conversion, you'll be able to convert another file!
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