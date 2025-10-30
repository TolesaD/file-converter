import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from utils.keyboard_utils import (
    get_main_menu_keyboard, 
    get_document_conversion_keyboard,
    get_image_conversion_keyboard,
    get_audio_conversion_keyboard,
    get_video_conversion_keyboard,
    get_presentation_conversion_keyboard,
    get_commands_keyboard
)
from database import db
from config import Config

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command with enhanced menu"""
    user = update.effective_user
    user_id = user.id
    
    # Register user in database
    db.register_user(user_id, user.first_name, user.username)
    
    welcome_text = f"""
🎯 *Welcome to Professional File Converter, {user.first_name}!*

I'm your AI-powered file conversion assistant with support for:

📷 *Images*: PNG, JPG, JPEG, BMP, GIF
🔊 *Audio*: MP3, WAV, AAC  
📹 *Video*: MP4, AVI, MOV, MKV
💼 *Documents*: PDF, DOCX, TXT, XLSX, ODT
🖼 *Presentations*: PPTX, PPT

✨ *Features:*
• High-quality conversions
• Smart format detection  
• Batch processing support
• Fast queue system
• Quality preservation

Simply send me a file or use the menu below to get started!
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    help_text = """
🆘 *File Converter Help Guide*

📁 *How to Convert Files:*
1. Send me any supported file
2. I'll automatically detect the format
3. Choose your desired output format
4. Wait for high-quality conversion

⚡ *Quick Commands:*
/start - Show main menu
/help - This help message  
/history - View your conversion history

📊 *Supported Conversions:*
• Images: PNG ↔ JPG ↔ JPEG ↔ BMP ↔ GIF ↔ PDF
• Audio: MP3 ↔ WAV ↔ AAC
• Video: MP4 ↔ AVI ↔ MOV ↔ MKV ↔ GIF  
• Documents: PDF ↔ DOCX ↔ TXT ↔ XLSX
• Presentations: PPTX/PPT → PDF

🔧 *Tips:*
• Maximum file size: 2GB
• Conversions are queued for fairness
• Quality is preserved whenever possible
• Contact admin for any issues

Ready to convert? Send me a file! 🚀
"""
    
    await update.message.reply_text(
        help_text,
        reply_markup=get_commands_keyboard(),
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries with improved flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"Callback from user {user_id}: {data}")
    
    # Clear any existing conversion data
    if data in ['main_menu', 'convert_file', 'commands']:
        context.user_data.pop('conversion_type', None)
        context.user_data.pop('output_format', None)
        context.user_data.pop('file_type', None)
    
    if data == 'main_menu':
        await show_main_menu(query, user_id)
        
    elif data == 'convert_file':
        await query.edit_message_text(
            "📁 *File Conversion*\n\n"
            "Please send me the file you want to convert.\n"
            "I support: Images, Audio, Video, Documents, Presentations",
            reply_markup=get_commands_keyboard(),
            parse_mode='Markdown'
        )
        
    elif data == 'commands':
        await show_commands_menu(query)
        
    elif data == 'history':
        await show_history(update, context)
        
    # Category menus
    elif data == 'menu_images':
        await show_image_conversions(query)
    elif data == 'menu_audio':
        await show_audio_conversions(query)  
    elif data == 'menu_video':
        await show_video_conversions(query)
    elif data == 'menu_documents':
        await show_document_conversions(query)
    elif data == 'menu_presentations':
        await show_presentation_conversions(query)
        
    # Image conversions
    elif data.startswith('convert_img_'):
        await handle_image_conversion(query, context, data)
        
    # Audio conversions  
    elif data.startswith('convert_audio_'):
        await handle_audio_conversion(query, context, data)
        
    # Video conversions
    elif data.startswith('convert_video_'):
        await handle_video_conversion(query, context, data)
        
    # Document conversions
    elif data.startswith('convert_doc_'):
        await handle_document_conversion(query, context, data)
        
    # Presentation conversions
    elif data.startswith('convert_presentation_'):
        await handle_presentation_conversion(query, context, data)
        
    # Auto conversion from suggestions
    elif data.startswith('auto_convert_'):
        await handle_auto_conversion(query, context, data)
    
    # Admin panel
    elif data == 'admin_panel':
        if user_id in Config.ADMIN_IDS:
            from handlers.admin import show_admin_panel
            await show_admin_panel(query)
        else:
            await query.edit_message_text("❌ Admin access required!")
    
    else:
        await query.edit_message_text("❌ Unknown command!")

async def show_main_menu(query, user_id):
    """Show main menu"""
    await query.edit_message_text(
        "🏠 *Main Menu*\n\n"
        "Choose a category or send me a file directly!",
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )

async def show_commands_menu(query):
    """Show commands menu"""
    await query.edit_message_text(
        "🔧 *Quick Commands*\n\n"
        "Use these options to navigate the bot:",
        reply_markup=get_commands_keyboard(),
        parse_mode='Markdown'
    )

async def show_image_conversions(query):
    """Show image conversion options"""
    await query.edit_message_text(
        "📷 *Image Conversions*\n\n"
        "Select conversion type:\n"
        "• PNG ↔ JPG/JPEG ↔ BMP ↔ GIF\n"
        "• All formats → PDF",
        reply_markup=get_image_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_audio_conversions(query):
    """Show audio conversion options"""
    await query.edit_message_text(
        "🔊 *Audio Conversions*\n\n"
        "Select conversion type:\n"
        "• MP3 ↔ WAV ↔ AAC",
        reply_markup=get_audio_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_video_conversions(query):
    """Show video conversion options"""
    await query.edit_message_text(
        "📹 *Video Conversions*\n\n"  
        "Select conversion type:\n"
        "• MP4 ↔ AVI ↔ MOV ↔ MKV\n"
        "• All formats → GIF",
        reply_markup=get_video_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_document_conversions(query):
    """Show document conversion options"""
    await query.edit_message_text(
        "💼 *Document Conversions*\n\n"
        "Select conversion type:\n"
        "• PDF ↔ DOCX ↔ TXT ↔ XLSX\n"
        "• ODT → PDF",
        reply_markup=get_document_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_presentation_conversions(query):
    """Show presentation conversion options"""
    await query.edit_message_text(
        "🖼 *Presentation Conversions*\n\n"
        "Select conversion type:\n"
        "• PPTX/PPT → PDF",
        reply_markup=get_presentation_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def handle_image_conversion(query, context, data):
    """Handle image conversion selection"""
    # Extract conversion details
    parts = data.split('_')
    if len(parts) >= 4:
        input_format = parts[2]
        output_format = parts[3]
        
        # Store conversion info
        context.user_data['conversion_type'] = 'image'
        context.user_data['output_format'] = output_format
        context.user_data['file_type'] = input_format
        
        await query.edit_message_text(
            f"🖼 *Image Conversion Selected*\n\n"
            f"Converting: `{input_format.upper()} → {output_format.upper()}`\n\n"
            f"Please send me an image file ({input_format.upper()}) to convert.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 Browse Categories", callback_data="menu_images"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]])
        )
    else:
        await query.edit_message_text("❌ Invalid conversion selection!")

async def handle_audio_conversion(query, context, data):
    """Handle audio conversion selection"""
    parts = data.split('_')
    if len(parts) >= 4:
        input_format = parts[2]
        output_format = parts[3]
        
        context.user_data['conversion_type'] = 'audio'
        context.user_data['output_format'] = output_format
        context.user_data['file_type'] = input_format
        
        await query.edit_message_text(
            f"🔊 *Audio Conversion Selected*\n\n"
            f"Converting: `{input_format.upper()} → {output_format.upper()}`\n\n"
            f"Please send me an audio file ({input_format.upper()}) to convert.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 Browse Categories", callback_data="menu_audio"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]])
        )

async def handle_video_conversion(query, context, data):
    """Handle video conversion selection"""
    parts = data.split('_')
    if len(parts) >= 4:
        input_format = parts[2]
        output_format = parts[3]
        
        context.user_data['conversion_type'] = 'video'
        context.user_data['output_format'] = output_format
        context.user_data['file_type'] = input_format
        
        await query.edit_message_text(
            f"📹 *Video Conversion Selected*\n\n"
            f"Converting: `{input_format.upper()} → {output_format.upper()}`\n\n"
            f"Please send me a video file ({input_format.upper()}) to convert.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 Browse Categories", callback_data="menu_video"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]])
        )

async def handle_document_conversion(query, context, data):
    """Handle document conversion selection"""
    parts = data.split('_')
    if len(parts) >= 4:
        input_format = parts[2]
        output_format = parts[3]
        
        context.user_data['conversion_type'] = 'document'
        context.user_data['output_format'] = output_format
        context.user_data['file_type'] = input_format
        
        await query.edit_message_text(
            f"💼 *Document Conversion Selected*\n\n"
            f"Converting: `{input_format.upper()} → {output_format.upper()}`\n\n"
            f"Please send me a document file ({input_format.upper()}) to convert.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 Browse Categories", callback_data="menu_documents"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]])
        )

async def handle_presentation_conversion(query, context, data):
    """Handle presentation conversion selection"""
    parts = data.split('_')
    if len(parts) >= 4:
        input_format = parts[2]
        output_format = parts[3]
        
        context.user_data['conversion_type'] = 'presentation'
        context.user_data['output_format'] = output_format
        context.user_data['file_type'] = input_format
        
        await query.edit_message_text(
            f"🖼 *Presentation Conversion Selected*\n\n"
            f"Converting: `{input_format.upper()} → {output_format.upper()}`\n\n"
            f"Please send me a presentation file ({input_format.upper()}) to convert.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 Browse Categories", callback_data="menu_presentations"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]])
        )

async def handle_auto_conversion(query, context, data):
    """Handle auto conversion from smart suggestions"""
    parts = data.split('_')
    if len(parts) >= 4:
        input_format = parts[2]
        output_format = parts[3]
        
        # Determine category from input format
        category = None
        for cat, formats in Config.SUPPORTED_FORMATS.items():
            if input_format in formats:
                category = cat
                break
        
        if category:
            context.user_data['conversion_type'] = category
            context.user_data['output_format'] = output_format
            context.user_data['file_type'] = input_format
            
            await query.edit_message_text(
                f"🎯 *Smart Conversion Selected*\n\n"
                f"Converting: `{input_format.upper()} → {output_format.upper()}`\n\n"
                f"Please send me a {category} file ({input_format.upper()}) to convert.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Convert Another", callback_data="convert_file"),
                    InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
                ]])
            )
        else:
            await query.edit_message_text("❌ Unsupported format!")

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user conversion history"""
    from handlers.history import show_user_history
    await show_user_history(update, context)

def detect_file_type(file_extension):
    """Detect file type and return category with proper naming"""
    file_extension = file_extension.lower().lstrip('.')
    
    for category, extensions in Config.SUPPORTED_FORMATS.items():
        if file_extension in extensions:
            category_name = Config.FORMAT_CATEGORIES.get(category, category.title())
            return category, category_name
    
    return 'unknown', 'Unknown File'

# Menu persistence after conversion
def get_continue_keyboard():
    """Get keyboard for continuing after conversion"""
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Another File", callback_data="convert_file")],
        [InlineKeyboardButton("📊 View History", callback_data="history")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)