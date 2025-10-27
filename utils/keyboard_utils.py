from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

def get_main_menu_keyboard(user_id=None):
    """Main menu with admin button only for admins"""
    keyboard = [
        [InlineKeyboardButton("📄 Document Conversion", callback_data="menu_documents")],
        [InlineKeyboardButton("🖼️ Image Conversion", callback_data="menu_images")],
        [InlineKeyboardButton("🎵 Audio Conversion", callback_data="menu_audio")],
        [InlineKeyboardButton("🎥 Video Conversion", callback_data="menu_video")],
        [InlineKeyboardButton("📊 My History", callback_data="history"),
         InlineKeyboardButton("ℹ️ Commands", callback_data="commands")],
    ]
    
    # Add admin button only for admins
    if user_id and user_id in Config.ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_commands_keyboard():
    keyboard = [
        [InlineKeyboardButton("/start - Start bot", callback_data="none")],
        [InlineKeyboardButton("/help - Get help", callback_data="none")],
        [InlineKeyboardButton("/history - View history", callback_data="none")],
        [InlineKeyboardButton("/stats - System stats", callback_data="none")],
        [InlineKeyboardButton("/admin - Admin panel", callback_data="none")],
        [InlineKeyboardButton("📋 Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_format_suggestions_keyboard(file_extension, file_type):
    """Show conversion options for detected file type"""
    keyboard = []
    
    # Get all possible target formats for this file type
    target_formats = Config.SUPPORTED_FORMATS.get(file_type, [])
    
    # Remove current format from targets
    target_formats = [fmt for fmt in target_formats if fmt != file_extension]
    
    # Create buttons in rows of 3
    row = []
    for i, target_format in enumerate(target_formats[:12]):  # Limit to 12 options
        row.append(InlineKeyboardButton(
            target_format.upper(), 
            callback_data=f"auto_convert_{file_extension}_{target_format}"
        ))
        if len(row) == 3 or i == len(target_formats[:12]) - 1:
            keyboard.append(row)
            row = []
    
    # Add back button
    keyboard.append([InlineKeyboardButton("📋 Back to Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_document_conversion_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 PDF to DOCX", callback_data="convert_pdf_docx"),
         InlineKeyboardButton("🖼️ PDF to Images", callback_data="convert_pdf_images")],
        [InlineKeyboardButton("📄 DOCX to PDF", callback_data="convert_docx_pdf"),
         InlineKeyboardButton("📊 Excel to PDF", callback_data="convert_excel_pdf")],
        [InlineKeyboardButton("📊 PPT to PDF", callback_data="convert_ppt_pdf"),
         InlineKeyboardButton("🖼️ Images to PDF", callback_data="convert_images_pdf")],
        [InlineKeyboardButton("📝 TXT to PDF", callback_data="convert_txt_pdf"),
         InlineKeyboardButton("🔒 Compress PDF", callback_data="compress_pdf")],
        [InlineKeyboardButton("🌐 HTML to PDF", callback_data="convert_html_pdf"),
         InlineKeyboardButton("📋 All Formats", callback_data="menu_all_documents")],
        [InlineKeyboardButton("📋 Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_all_documents_keyboard():
    """All document format conversions"""
    formats = Config.SUPPORTED_FORMATS['document']
    keyboard = []
    row = []
    
    for i, fmt in enumerate(formats):
        row.append(InlineKeyboardButton(fmt.upper(), callback_data=f"doc_format_{fmt}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Documents", callback_data="menu_documents")])
    return InlineKeyboardMarkup(keyboard)

def get_document_format_keyboard(source_format):
    """Target formats for a specific document format"""
    formats = [f for f in Config.SUPPORTED_FORMATS['document'] if f != source_format]
    keyboard = []
    row = []
    
    for i, target_fmt in enumerate(formats):
        row.append(InlineKeyboardButton(
            target_fmt.upper(), 
            callback_data=f"convert_doc_{source_format}_{target_fmt}"
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Documents", callback_data="menu_documents")])
    return InlineKeyboardMarkup(keyboard)

def get_image_conversion_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔄 JPG to PNG", callback_data="convert_jpg_png"),
         InlineKeyboardButton("🔄 PNG to JPG", callback_data="convert_png_jpg")],
        [InlineKeyboardButton("🔄 WEBP to JPG", callback_data="convert_webp_jpg"),
         InlineKeyboardButton("📏 Resize Image", callback_data="resize_image")],
        [InlineKeyboardButton("🗜️ Compress Image", callback_data="compress_image"),
         InlineKeyboardButton("🎨 Apply Filter", callback_data="menu_filters")],
        [InlineKeyboardButton("✂️ Crop Image", callback_data="crop_image"),
         InlineKeyboardButton("🔄 Rotate Image", callback_data="rotate_image")],
        [InlineKeyboardButton("🖼️ All Formats", callback_data="menu_all_images"),
         InlineKeyboardButton("📋 Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_all_images_keyboard():
    """All image format conversions"""
    formats = Config.SUPPORTED_FORMATS['image']
    keyboard = []
    row = []
    
    for i, fmt in enumerate(formats):
        row.append(InlineKeyboardButton(fmt.upper(), callback_data=f"img_format_{fmt}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Images", callback_data="menu_images")])
    return InlineKeyboardMarkup(keyboard)

def get_image_format_keyboard(source_format):
    """Target formats for a specific image format"""
    formats = [f for f in Config.SUPPORTED_FORMATS['image'] if f != source_format]
    keyboard = []
    row = []
    
    for i, target_fmt in enumerate(formats):
        row.append(InlineKeyboardButton(
            target_fmt.upper(), 
            callback_data=f"convert_img_{source_format}_{target_fmt}"
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Images", callback_data="menu_images")])
    return InlineKeyboardMarkup(keyboard)

def get_image_filters_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔵 Blur", callback_data="filter_blur"),
         InlineKeyboardButton("🔶 Sharpen", callback_data="filter_sharpen")],
        [InlineKeyboardButton("⚫ Grayscale", callback_data="filter_grayscale"),
         InlineKeyboardButton("🏔️ Emboss", callback_data="filter_emboss")],
        [InlineKeyboardButton("📐 Contour", callback_data="filter_contour"),
         InlineKeyboardButton("🔄 Invert", callback_data="filter_invert")],
        [InlineKeyboardButton("📋 Back to Images", callback_data="menu_images")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_audio_conversion_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔄 MP3 to WAV", callback_data="convert_mp3_wav"),
         InlineKeyboardButton("🔄 WAV to MP3", callback_data="convert_wav_mp3")],
        [InlineKeyboardButton("🗜️ Compress Audio", callback_data="compress_audio"),
         InlineKeyboardButton("✂️ Trim Audio", callback_data="trim_audio")],
        [InlineKeyboardButton("🎵 Change Speed", callback_data="change_speed"),
         InlineKeyboardButton("🎥 Extract Audio", callback_data="extract_audio")],
        [InlineKeyboardButton("🎵 All Formats", callback_data="menu_all_audio"),
         InlineKeyboardButton("📋 Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_all_audio_keyboard():
    """All audio format conversions"""
    formats = Config.SUPPORTED_FORMATS['audio']
    keyboard = []
    row = []
    
    for i, fmt in enumerate(formats):
        row.append(InlineKeyboardButton(fmt.upper(), callback_data=f"audio_format_{fmt}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Audio", callback_data="menu_audio")])
    return InlineKeyboardMarkup(keyboard)

def get_audio_format_keyboard(source_format):
    """Target formats for a specific audio format"""
    formats = [f for f in Config.SUPPORTED_FORMATS['audio'] if f != source_format]
    keyboard = []
    row = []
    
    for i, target_fmt in enumerate(formats):
        row.append(InlineKeyboardButton(
            target_fmt.upper(), 
            callback_data=f"convert_audio_{source_format}_{target_fmt}"
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Audio", callback_data="menu_audio")])
    return InlineKeyboardMarkup(keyboard)

def get_video_conversion_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔄 MP4 to GIF", callback_data="convert_mp4_gif"),
         InlineKeyboardButton("🗜️ Compress Video", callback_data="compress_video")],
        [InlineKeyboardButton("🎵 Extract Audio", callback_data="extract_audio"),
         InlineKeyboardButton("✂️ Trim Video", callback_data="trim_video")],
        [InlineKeyboardButton("🎥 All Formats", callback_data="menu_all_video"),
         InlineKeyboardButton("📋 Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_all_video_keyboard():
    """All video format conversions"""
    formats = Config.SUPPORTED_FORMATS['video']
    keyboard = []
    row = []
    
    for i, fmt in enumerate(formats):
        row.append(InlineKeyboardButton(fmt.upper(), callback_data=f"video_format_{fmt}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Video", callback_data="menu_video")])
    return InlineKeyboardMarkup(keyboard)

def get_video_format_keyboard(source_format):
    """Target formats for a specific video format"""
    formats = [f for f in Config.SUPPORTED_FORMATS['video'] if f != source_format]
    keyboard = []
    row = []
    
    for i, target_fmt in enumerate(formats):
        row.append(InlineKeyboardButton(
            target_fmt.upper(), 
            callback_data=f"convert_video_{source_format}_{target_fmt}"
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 Back to Video", callback_data="menu_video")])
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 System Stats", callback_data="admin_stats"),
         InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton("📈 Reports", callback_data="admin_reports")],
        [InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_refresh"),
         InlineKeyboardButton("📋 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_stats_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Real-time Stats", callback_data="admin_stats_live"),
         InlineKeyboardButton("📈 Daily Report", callback_data="admin_stats_daily")],
        [InlineKeyboardButton("👥 User Analytics", callback_data="admin_stats_users"),
         InlineKeyboardButton("📁 Format Usage", callback_data="admin_stats_formats")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
    return InlineKeyboardMarkup(keyboard)