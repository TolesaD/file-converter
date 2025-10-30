from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_main_menu_keyboard(user_id):
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📁 Convert File", callback_data="convert_file")],
        [InlineKeyboardButton("📤 Upload Any File", callback_data="upload_now")],
        [InlineKeyboardButton("📊 History", callback_data="history")],
    ]
    
    # Add admin panel for admins
    if user_id in Config.ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_format_suggestions_keyboard(file_extension, file_type):
    """Get smart conversion suggestions for a file type - FIXED"""
    keyboard = []
    
    # Get supported formats based on file type
    supported_formats = get_smart_suggestions(file_extension, file_type)
    
    # Create buttons for each supported conversion
    row = []
    for i, target_format in enumerate(supported_formats):
        if target_format != file_extension:  # Don't suggest converting to same format
            # Use emojis based on target format type
            emoji = _get_format_emoji(target_format)
            button = InlineKeyboardButton(
                f"{emoji} to {target_format.upper()}",
                callback_data=f"auto_convert_{file_extension}_{target_format}"
            )
            row.append(button)
            
            # Create new row every 2 buttons for better layout
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    # Add any remaining buttons
    if row:
        keyboard.append(row)
    
    # Add navigation buttons
    keyboard.append([InlineKeyboardButton("🔍 Browse All Categories", callback_data="convert_file")])
    keyboard.append([InlineKeyboardButton("📤 Upload Different File", callback_data="upload_now")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_smart_suggestions(file_extension, file_type):
    """Get smart conversion suggestions based on file type"""
    # Smart suggestion mapping
    suggestions_map = {
        'image': {
            'common': ['jpg', 'png', 'pdf', 'bmp'],
            'png': ['jpg', 'jpeg', 'pdf', 'bmp', 'gif'],
            'jpg': ['png', 'jpeg', 'pdf', 'bmp', 'gif'], 
            'jpeg': ['png', 'jpg', 'pdf', 'bmp', 'gif'],
            'gif': ['png', 'jpg', 'jpeg', 'pdf', 'bmp'],
            'bmp': ['png', 'jpg', 'jpeg', 'pdf', 'gif'],
            'webp': ['png', 'jpg', 'jpeg', 'pdf']
        },
        'audio': {
            'common': ['mp3', 'wav', 'aac'],
            'mp3': ['wav', 'aac'],
            'wav': ['mp3', 'aac'],
            'aac': ['mp3', 'wav'],
            'ogg': ['mp3', 'wav'],
            'flac': ['mp3', 'wav']
        },
        'video': {
            'common': ['mp4', 'avi', 'mov', 'mkv', 'gif'],
            'mp4': ['avi', 'mov', 'mkv', 'gif'],
            'avi': ['mp4', 'mov', 'mkv'],
            'mov': ['mp4', 'avi', 'mkv'],
            'mkv': ['mp4', 'avi', 'mov'],
            'webm': ['mp4', 'avi', 'mov']
        },
        'document': {
            'common': ['pdf', 'docx', 'txt', 'xlsx'],
            'pdf': ['docx', 'txt', 'xlsx', 'jpg', 'png'],
            'docx': ['pdf', 'txt', 'xlsx'],
            'txt': ['pdf', 'docx', 'xlsx'],
            'xlsx': ['pdf', 'txt', 'docx'],
            'odt': ['pdf', 'docx', 'txt']
        },
        'presentation': {
            'common': ['pdf'],
            'pptx': ['pdf'],
            'ppt': ['pdf']
        }
    }
    
    # Get suggestions for the specific file type
    file_type_suggestions = suggestions_map.get(file_type, {})
    specific_suggestions = file_type_suggestions.get(file_extension, [])
    common_suggestions = file_type_suggestions.get('common', [])
    
    # Combine and remove duplicates
    all_suggestions = list(set(specific_suggestions + common_suggestions))
    
    # Remove current format
    all_suggestions = [fmt for fmt in all_suggestions if fmt != file_extension]
    
    # Sort by most common formats first
    common_formats = ['pdf', 'jpg', 'png', 'mp3', 'mp4', 'docx', 'txt', 'wav']
    sorted_suggestions = [fmt for fmt in common_formats if fmt in all_suggestions]
    sorted_suggestions.extend([fmt for fmt in all_suggestions if fmt not in common_formats])
    
    return sorted_suggestions[:8]  # Limit to 8 suggestions

def _get_format_emoji(format_type):
    """Get appropriate emoji for file format"""
    emoji_map = {
        'pdf': '📄',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'bmp': '🖼️', 'webp': '🖼️',
        'mp3': '🎵', 'wav': '🎵', 'aac': '🎵', 'ogg': '🎵', 'flac': '🎵',
        'mp4': '🎥', 'avi': '🎥', 'mov': '🎥', 'mkv': '🎥', 'webm': '🎥',
        'docx': '📝', 'txt': '📝', 'xlsx': '📊', 'odt': '📝',
        'pptx': '🖼️', 'ppt': '🖼️'
    }
    return emoji_map.get(format_type, '📁')

def get_document_conversion_keyboard():
    """Get document conversion options"""
    keyboard = [
        [InlineKeyboardButton("📄 PDF to DOCX", callback_data="convert_doc_pdf_docx")],
        [InlineKeyboardButton("📄 PDF to TXT", callback_data="convert_doc_pdf_txt")],
        [InlineKeyboardButton("📄 PDF to XLSX", callback_data="convert_doc_pdf_xlsx")],
        [InlineKeyboardButton("📄 DOCX to PDF", callback_data="convert_doc_docx_pdf")],
        [InlineKeyboardButton("📄 DOCX to TXT", callback_data="convert_doc_docx_txt")],
        [InlineKeyboardButton("📄 TXT to PDF", callback_data="convert_doc_txt_pdf")],
        [InlineKeyboardButton("📄 TXT to DOCX", callback_data="convert_doc_txt_docx")],
        [InlineKeyboardButton("📊 XLSX to PDF", callback_data="convert_doc_xlsx_pdf")],
        [InlineKeyboardButton("📄 ODT to PDF", callback_data="convert_doc_odt_pdf")],
        [InlineKeyboardButton("📤 Upload Any File", callback_data="upload_now")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_image_conversion_keyboard():
    """Get image conversion options"""
    keyboard = [
        [InlineKeyboardButton("🖼 PNG to JPG", callback_data="convert_img_png_jpg")],
        [InlineKeyboardButton("🖼 JPG to PNG", callback_data="convert_img_jpg_png")],
        [InlineKeyboardButton("🖼 PNG to PDF", callback_data="convert_img_png_pdf")],
        [InlineKeyboardButton("🖼 JPG to PDF", callback_data="convert_img_jpg_pdf")],
        [InlineKeyboardButton("🖼 GIF to PNG", callback_data="convert_img_gif_png")],
        [InlineKeyboardButton("🖼 GIF to JPG", callback_data="convert_img_gif_jpg")],
        [InlineKeyboardButton("📤 Upload Any Image", callback_data="upload_now")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_audio_conversion_keyboard():
    """Get audio conversion options"""
    keyboard = [
        [InlineKeyboardButton("🎵 MP3 to WAV", callback_data="convert_audio_mp3_wav")],
        [InlineKeyboardButton("🎵 WAV to MP3", callback_data="convert_audio_wav_mp3")],
        [InlineKeyboardButton("🎵 MP3 to AAC", callback_data="convert_audio_mp3_aac")],
        [InlineKeyboardButton("🎵 AAC to MP3", callback_data="convert_audio_aac_mp3")],
        [InlineKeyboardButton("📤 Upload Any Audio", callback_data="upload_now")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_video_conversion_keyboard():
    """Get video conversion options"""
    keyboard = [
        [InlineKeyboardButton("🎥 MP4 to AVI", callback_data="convert_video_mp4_avi")],
        [InlineKeyboardButton("🎥 AVI to MP4", callback_data="convert_video_avi_mp4")],
        [InlineKeyboardButton("🎥 MP4 to MOV", callback_data="convert_video_mp4_mov")],
        [InlineKeyboardButton("🎥 MP4 to GIF", callback_data="convert_video_mp4_gif")],
        [InlineKeyboardButton("📤 Upload Any Video", callback_data="upload_now")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_presentation_conversion_keyboard():
    """Get presentation conversion options"""
    keyboard = [
        [InlineKeyboardButton("🖼 PPTX to PDF", callback_data="convert_presentation_pptx_pdf")],
        [InlineKeyboardButton("🖼 PPT to PDF", callback_data="convert_presentation_ppt_pdf")],
        [InlineKeyboardButton("📤 Upload Any Presentation", callback_data="upload_now")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

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

def get_continue_menu_keyboard():
    """Get keyboard for continuing after conversion"""
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Another File", callback_data="convert_file")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_commands_keyboard():
    """Get commands keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        [InlineKeyboardButton("📊 View History", callback_data="history")],
    ]
    return InlineKeyboardMarkup(keyboard)