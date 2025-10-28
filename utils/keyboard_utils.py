from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from converters.converter_router import converter_router

def get_main_menu_keyboard(user_id):
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📷 Convert Images", callback_data="menu_images")],
        [InlineKeyboardButton("🔊 Convert Audio", callback_data="menu_audio")],
        [InlineKeyboardButton("📹 Convert Video", callback_data="menu_video")],
        [InlineKeyboardButton("💼 Convert Documents", callback_data="menu_documents")],
        [InlineKeyboardButton("📋 Commands", callback_data="commands")],
        [InlineKeyboardButton("📊 History", callback_data="history")],
    ]
    
    # Add admin panel for admins
    if user_id in Config.ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_commands_keyboard():
    """Get commands keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        [InlineKeyboardButton("📊 View History", callback_data="history")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_document_conversion_keyboard():
    """Get document conversion options"""
    keyboard = [
        [InlineKeyboardButton("📄 PDF to DOCX", callback_data="convert_doc_pdf_docx")],
        [InlineKeyboardButton("📄 PDF to TXT", callback_data="convert_doc_pdf_txt")],
        [InlineKeyboardButton("📄 DOCX to PDF", callback_data="convert_doc_docx_pdf")],
        [InlineKeyboardButton("📄 DOCX to TXT", callback_data="convert_doc_docx_txt")],
        [InlineKeyboardButton("📄 TXT to PDF", callback_data="convert_doc_txt_pdf")],
        [InlineKeyboardButton("📄 TXT to DOCX", callback_data="convert_doc_txt_docx")],
        [InlineKeyboardButton("📊 Excel to PDF", callback_data="convert_doc_xlsx_pdf")],
        [InlineKeyboardButton("📄 ODT to PDF", callback_data="convert_doc_odt_pdf")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_image_conversion_keyboard():
    """Get image conversion options"""
    keyboard = [
        [InlineKeyboardButton("🖼️ PNG to JPG", callback_data="convert_img_png_jpg")],
        [InlineKeyboardButton("🖼️ JPG to PNG", callback_data="convert_img_jpg_png")],
        [InlineKeyboardButton("🖼️ JPG to BMP", callback_data="convert_img_jpg_bmp")],
        [InlineKeyboardButton("🖼️ PNG to BMP", callback_data="convert_img_png_bmp")],
        [InlineKeyboardButton("🖼️ BMP to JPG", callback_data="convert_img_bmp_jpg")],
        [InlineKeyboardButton("🖼️ BMP to PNG", callback_data="convert_img_bmp_png")],
        [InlineKeyboardButton("🖼️ Any to PDF", callback_data="convert_img_image_pdf")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_audio_conversion_keyboard():
    """Get audio conversion options"""
    keyboard = [
        [InlineKeyboardButton("🎵 MP3 to WAV", callback_data="convert_audio_mp3_wav")],
        [InlineKeyboardButton("🎵 MP3 to AAC", callback_data="convert_audio_mp3_aac")],
        [InlineKeyboardButton("🎵 WAV to MP3", callback_data="convert_audio_wav_mp3")],
        [InlineKeyboardButton("🎵 WAV to AAC", callback_data="convert_audio_wav_aac")],
        [InlineKeyboardButton("🎵 AAC to MP3", callback_data="convert_audio_aac_mp3")],
        [InlineKeyboardButton("🎵 AAC to WAV", callback_data="convert_audio_aac_wav")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_video_conversion_keyboard():
    """Get video conversion options"""
    keyboard = [
        [InlineKeyboardButton("🎥 MP4 to AVI", callback_data="convert_video_mp4_avi")],
        [InlineKeyboardButton("🎥 MP4 to MOV", callback_data="convert_video_mp4_mov")],
        [InlineKeyboardButton("🎥 MP4 to MKV", callback_data="convert_video_mp4_mkv")],
        [InlineKeyboardButton("🎥 AVI to MP4", callback_data="convert_video_avi_mp4")],
        [InlineKeyboardButton("🎥 MOV to MP4", callback_data="convert_video_mov_mp4")],
        [InlineKeyboardButton("🎥 MKV to MP4", callback_data="convert_video_mkv_mp4")],
        [InlineKeyboardButton("🎥 MP4 to GIF", callback_data="convert_video_mp4_gif")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_format_suggestions_keyboard(file_extension, file_type):
    """Get smart conversion suggestions for a file type"""
    keyboard = []
    
    # Get supported conversions from router
    import asyncio
    try:
        # Run the async function in a sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        supported_formats = loop.run_until_complete(
            converter_router.get_supported_conversions(file_extension)
        )
        loop.close()
    except:
        # Fallback if async call fails
        supported_formats = get_fallback_suggestions(file_extension, file_type)
    
    # Create buttons for each supported conversion
    row = []
    for i, target_format in enumerate(supported_formats):
        if target_format != file_extension:  # Don't suggest converting to same format
            button = InlineKeyboardButton(
                f"➡️ {target_format.upper()}",
                callback_data=f"auto_convert_{file_extension}_{target_format}"
            )
            row.append(button)
            
            # Create new row every 2 buttons
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    # Add any remaining buttons
    if row:
        keyboard.append(row)
    
    # Add navigation buttons
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    keyboard.append([InlineKeyboardButton("📋 Browse Categories", callback_data="commands")])
    
    return InlineKeyboardMarkup(keyboard)

def get_fallback_suggestions(file_extension, file_type):
    """Fallback suggestions if router fails"""
    suggestions_map = {
        'image': ['jpg', 'png', 'pdf', 'bmp', 'gif'],
        'audio': ['mp3', 'wav', 'aac'],
        'video': ['mp4', 'avi', 'mov', 'mkv', 'gif'],
        'document': ['pdf', 'docx', 'txt'],
        'presentation': ['pdf']
    }
    
    # Remove current format from suggestions
    file_extension = file_extension.lower()
    suggestions = suggestions_map.get(file_type, [])
    return [fmt for fmt in suggestions if fmt != file_extension][:6]

def get_admin_keyboard():
    """Get admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 System Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📈 Reports", callback_data="admin_reports")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_stats_keyboard():
    """Get admin statistics keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔄 Live Stats", callback_data="admin_stats_live")],
        [InlineKeyboardButton("📅 Daily Report", callback_data="admin_stats_daily")],
        [InlineKeyboardButton("👥 User Analytics", callback_data="admin_stats_users")],
        [InlineKeyboardButton("📁 Format Usage", callback_data="admin_stats_formats")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Get cancel operation keyboard"""
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")],
    ]
    return InlineKeyboardMarkup(keyboard)