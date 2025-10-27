from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import Config
from utils.keyboard_utils import (
    get_main_menu_keyboard, 
    get_commands_keyboard,
    get_document_conversion_keyboard,
    get_image_conversion_keyboard,
    get_image_filters_keyboard,
    get_audio_conversion_keyboard,
    get_video_conversion_keyboard,
    get_all_documents_keyboard,
    get_all_images_keyboard,
    get_all_audio_keyboard,
    get_all_video_keyboard,
    get_document_format_keyboard,
    get_image_format_keyboard,
    get_audio_format_keyboard,
    get_video_format_keyboard,
    get_format_suggestions_keyboard,
    get_admin_keyboard
)
import logging
import os

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu"""
    user = update.effective_user
    user_id = user.id
    
    # Clear any existing context data
    context.user_data.clear()
    
    # Add user to database
    db.add_user(user_id, user.username, user.first_name, user.last_name)
    
    welcome_text = f"""
👋 Welcome *{user.first_name}* to the *Smart File Converter Bot*! 🚀

*Smart Features:*
• 🧠 Automatic file type detection
• 💡 Smart conversion suggestions  
• ⚡ Fast multi-format support
• 📊 Real-time progress updates

*Supported Categories:*
📷 Images (20 formats) - PNG, JPG, WEBP, SVG, RAW...
🔊 Audio (13 formats) - MP3, WAV, FLAC, OGG, M4A...
📹 Video (16 formats) - MP4, AVI, MKV, MOV, WEBM...
💼 Documents (12 formats) - PDF, DOCX, XLSX, TXT, HTML...
🖼 Presentations (12 formats) - PPT, PPTX, ODP, KEY...

*Just upload any file and I'll automatically detect its type and show conversion options!*
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help information"""
    user_id = update.effective_user.id
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
    from handlers.history import show_history as show_user_history
    await show_user_history(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    is_admin = user_id in Config.ADMIN_IDS
    
    logger.info(f"Callback received: {callback_data} from user {user_id}")
    
    # Handle admin-only callbacks
    admin_callbacks = ["admin_stats", "admin_stats_live", "admin_stats_daily", 
                      "admin_stats_users", "admin_stats_formats", "admin_users",
                      "admin_broadcast", "admin_reports", "admin_refresh", "admin_panel",
                      "admin_view_users", "admin_banned_users"]
    
    if any(callback_data.startswith(cb) for cb in admin_callbacks):
        if not is_admin:
            await query.edit_message_text("❌ Access denied. Admin only.")
            return
        # Route to admin handler
        from handlers.admin import handle_admin_callback
        await handle_admin_callback(update, context)
        return
    
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
    elif callback_data == "menu_filters":
        await show_filters_menu(query)
    elif callback_data == "menu_all_documents":
        await show_all_documents_menu(query)
    elif callback_data == "menu_all_images":
        await show_all_images_menu(query)
    elif callback_data == "menu_all_audio":
        await show_all_audio_menu(query)
    elif callback_data == "menu_all_video":
        await show_all_video_menu(query)
    elif callback_data.startswith("doc_format_"):
        source_format = callback_data.replace("doc_format_", "")
        await show_document_format_menu(query, source_format)
    elif callback_data.startswith("img_format_"):
        source_format = callback_data.replace("img_format_", "")
        await show_image_format_menu(query, source_format)
    elif callback_data.startswith("audio_format_"):
        source_format = callback_data.replace("audio_format_", "")
        await show_audio_format_menu(query, source_format)
    elif callback_data.startswith("video_format_"):
        source_format = callback_data.replace("video_format_", "")
        await show_video_format_menu(query, source_format)
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
    elif callback_data.startswith("auto_convert_"):
        parts = callback_data.replace("auto_convert_", "").split("_")
        if len(parts) == 2:
            await start_auto_conversion(query, context, parts[0], parts[1])
    elif callback_data.startswith("convert_") or callback_data.startswith("filter_") or callback_data in ["compress_image", "resize_image", "crop_image", "rotate_image", "compress_audio", "trim_audio", "change_speed", "extract_audio", "compress_video", "trim_video", "compress_pdf"]:
        await start_conversion(query, context, callback_data)
    elif callback_data == "admin_panel":
        await show_admin_panel(query, user_id)
    elif callback_data == "history":
        from handlers.history import handle_history_callback
        await handle_history_callback(update, context)
    elif callback_data == "none":
        pass
    else:
        logger.warning(f"Unhandled callback: {callback_data}")

async def show_main_menu(query, user_id):
    await query.edit_message_text(
        "🏠 *Main Menu*\nChoose what you want to convert:",
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
    await query.edit_message_text(
        "📄 *Document Conversion*\nSelect conversion type:",
        reply_markup=get_document_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_all_documents_menu(query):
    await query.edit_message_text(
        "💼 *All Document Formats*\nSelect source format:",
        reply_markup=get_all_documents_keyboard(),
        parse_mode='Markdown'
    )

async def show_document_format_menu(query, source_format):
    await query.edit_message_text(
        f"💼 *Convert {source_format.upper()} to:*\nChoose target format:",
        reply_markup=get_document_format_keyboard(source_format),
        parse_mode='Markdown'
    )

async def show_image_menu(query):
    await query.edit_message_text(
        "🖼️ *Image Conversion*\nSelect conversion type:",
        reply_markup=get_image_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_all_images_menu(query):
    await query.edit_message_text(
        "📷 *All Image Formats*\nSelect source format:",
        reply_markup=get_all_images_keyboard(),
        parse_mode='Markdown'
    )

async def show_image_format_menu(query, source_format):
    await query.edit_message_text(
        f"📷 *Convert {source_format.upper()} to:*\nChoose target format:",
        reply_markup=get_image_format_keyboard(source_format),
        parse_mode='Markdown'
    )

async def show_filters_menu(query):
    await query.edit_message_text(
        "🎨 *Image Filters*\nSelect a filter to apply:",
        reply_markup=get_image_filters_keyboard(),
        parse_mode='Markdown'
    )

async def show_audio_menu(query):
    await query.edit_message_text(
        "🎵 *Audio Conversion*\nSelect conversion type:",
        reply_markup=get_audio_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_all_audio_menu(query):
    await query.edit_message_text(
        "🔊 *All Audio Formats*\nSelect source format:",
        reply_markup=get_all_audio_keyboard(),
        parse_mode='Markdown'
    )

async def show_audio_format_menu(query, source_format):
    await query.edit_message_text(
        f"🔊 *Convert {source_format.upper()} to:*\nChoose target format:",
        reply_markup=get_audio_format_keyboard(source_format),
        parse_mode='Markdown'
    )

async def show_video_menu(query):
    await query.edit_message_text(
        "🎥 *Video Conversion*\nSelect conversion type:",
        reply_markup=get_video_conversion_keyboard(),
        parse_mode='Markdown'
    )

async def show_all_video_menu(query):
    await query.edit_message_text(
        "📹 *All Video Formats*\nSelect source format:",
        reply_markup=get_all_video_keyboard(),
        parse_mode='Markdown'
    )

async def show_video_format_menu(query, source_format):
    await query.edit_message_text(
        f"📹 *Convert {source_format.upper()} to:*\nChoose target format:",
        reply_markup=get_video_format_keyboard(source_format),
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
    
    logger.info(f"Starting auto conversion: {source_format} -> {target_format}")
    
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

async def start_conversion(query, context, conversion_type):
    """Start manual conversion process"""
    conversion_map = {
        'convert_pdf_docx': ('PDF to DOCX', 'pdf', 'docx'),
        'convert_pdf_images': ('PDF to Images', 'pdf', 'jpg'),
        'convert_docx_pdf': ('DOCX to PDF', 'docx', 'pdf'),
        'convert_images_pdf': ('Images to PDF', 'image', 'pdf'),
        'convert_excel_pdf': ('Excel to PDF', 'xlsx', 'pdf'),
        'convert_ppt_pdf': ('PowerPoint to PDF', 'pptx', 'pdf'),
        'convert_txt_pdf': ('Text to PDF', 'txt', 'pdf'),
        'convert_html_pdf': ('HTML to PDF', 'html', 'pdf'),
        'convert_jpg_png': ('JPG to PNG', 'jpg', 'png'),
        'convert_png_jpg': ('PNG to JPG', 'png', 'jpg'),
        'convert_webp_jpg': ('WEBP to JPG', 'webp', 'jpg'),
        'convert_mp3_wav': ('MP3 to WAV', 'mp3', 'wav'),
        'convert_wav_mp3': ('WAV to MP3', 'wav', 'mp3'),
        'convert_mp4_gif': ('MP4 to GIF', 'mp4', 'gif'),
        'compress_pdf': ('Compress PDF', 'pdf', 'pdf'),
        'compress_image': ('Compress Image', 'image', 'same'),
        'compress_audio': ('Compress Audio', 'audio', 'mp3'),
        'compress_video': ('Compress Video', 'video', 'mp4'),
        'resize_image': ('Resize Image', 'image', 'same'),
        'crop_image': ('Crop Image', 'image', 'same'),
        'rotate_image': ('Rotate Image', 'image', 'same'),
        'trim_audio': ('Trim Audio', 'audio', 'same'),
        'trim_video': ('Trim Video', 'video', 'same'),
        'change_speed': ('Change Audio Speed', 'audio', 'same'),
        'extract_audio': ('Extract Audio from Video', 'video', 'mp3'),
        'filter_blur': ('Apply Blur Filter', 'image', 'same'),
        'filter_sharpen': ('Apply Sharpen Filter', 'image', 'same'),
        'filter_grayscale': ('Apply Grayscale Filter', 'image', 'same'),
        'filter_emboss': ('Apply Emboss Filter', 'image', 'same'),
        'filter_contour': ('Apply Contour Filter', 'image', 'same'),
        'filter_invert': ('Apply Invert Filter', 'image', 'same'),
    }
    
    if conversion_type in conversion_map:
        conversion_name, input_format, output_format = conversion_map[conversion_type]
        context.user_data['conversion_type'] = conversion_type
        context.user_data['input_format'] = input_format
        context.user_data['output_format'] = output_format
        
        message_text = f"🔄 *{conversion_name}*\n\nPlease upload your {input_format.upper()} file."
        
        await query.edit_message_text(message_text, parse_mode='Markdown')
    else:
        await query.edit_message_text("❌ Conversion type not supported yet.")

def detect_file_type(file_extension):
    """Detect file type category"""
    file_extension = file_extension.lower()
    
    for file_type, extensions in Config.SUPPORTED_FORMATS.items():
        if file_extension in extensions:
            return file_type, Config.FORMAT_CATEGORIES[file_type]
    
    return 'unknown', '📁 Unknown'