from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from converters.converter_router import converter_router
import asyncio
import logging

logger = logging.getLogger(__name__)

def get_main_menu_keyboard(user_id):
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📁 Convert File", callback_data="convert_file")],
        [InlineKeyboardButton("📷 Convert Images", callback_data="menu_images")],
        [InlineKeyboardButton("🔊 Convert Audio", callback_data="menu_audio")],
        [InlineKeyboardButton("📹 Convert Video", callback_data="menu_video")],
        [InlineKeyboardButton("💼 Convert Documents", callback_data="menu_documents")],
        [InlineKeyboardButton("🖼 Convert Presentations", callback_data="menu_presentations")],
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
    """Get document conversion options - ALL 12 RELIABLE CONVERSIONS"""
    keyboard = [
        # PDF conversions
        [InlineKeyboardButton("📄 PDF to DOCX", callback_data="convert_doc_pdf_docx")],
        [InlineKeyboardButton("📄 PDF to TXT", callback_data="convert_doc_pdf_txt")],
        [InlineKeyboardButton("📄 PDF to XLSX", callback_data="convert_doc_pdf_xlsx")],
        
        # DOCX conversions
        [InlineKeyboardButton("📄 DOCX to PDF", callback_data="convert_doc_docx_pdf")],
        [InlineKeyboardButton("📄 DOCX to TXT", callback_data="convert_doc_docx_txt")],
        
        # TXT conversions
        [InlineKeyboardButton("📄 TXT to PDF", callback_data="convert_doc_txt_pdf")],
        [InlineKeyboardButton("📄 TXT to DOCX", callback_data="convert_doc_txt_docx")],
        
        # Excel conversions
        [InlineKeyboardButton("📊 XLSX to PDF", callback_data="convert_doc_xlsx_pdf")],
        
        # ODT conversions
        [InlineKeyboardButton("📄 ODT to PDF", callback_data="convert_doc_odt_pdf")],
        
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_image_conversion_keyboard():
    """Get image conversion options - ALL 20 COMBINATIONS"""
    keyboard = [
        # PNG conversions
        [InlineKeyboardButton("🖼 PNG to JPG", callback_data="convert_img_png_jpg")],
        [InlineKeyboardButton("🖼 PNG to JPEG", callback_data="convert_img_png_jpeg")],
        [InlineKeyboardButton("🖼 PNG to BMP", callback_data="convert_img_png_bmp")],
        [InlineKeyboardButton("🖼 PNG to GIF", callback_data="convert_img_png_gif")],
        
        # JPG conversions
        [InlineKeyboardButton("🖼 JPG to PNG", callback_data="convert_img_jpg_png")],
        [InlineKeyboardButton("🖼 JPG to JPEG", callback_data="convert_img_jpg_jpeg")],
        [InlineKeyboardButton("🖼 JPG to BMP", callback_data="convert_img_jpg_bmp")],
        [InlineKeyboardButton("🖼 JPG to GIF", callback_data="convert_img_jpg_gif")],
        
        # JPEG conversions
        [InlineKeyboardButton("🖼 JPEG to PNG", callback_data="convert_img_jpeg_png")],
        [InlineKeyboardButton("🖼 JPEG to JPG", callback_data="convert_img_jpeg_jpg")],
        [InlineKeyboardButton("🖼 JPEG to BMP", callback_data="convert_img_jpeg_bmp")],
        [InlineKeyboardButton("🖼 JPEG to GIF", callback_data="convert_img_jpeg_gif")],
        
        # BMP conversions
        [InlineKeyboardButton("🖼 BMP to PNG", callback_data="convert_img_bmp_png")],
        [InlineKeyboardButton("🖼 BMP to JPG", callback_data="convert_img_bmp_jpg")],
        [InlineKeyboardButton("🖼 BMP to JPEG", callback_data="convert_img_bmp_jpeg")],
        [InlineKeyboardButton("🖼 BMP to GIF", callback_data="convert_img_bmp_gif")],
        
        # GIF conversions
        [InlineKeyboardButton("🖼 GIF to PNG", callback_data="convert_img_gif_png")],
        [InlineKeyboardButton("🖼 GIF to JPG", callback_data="convert_img_gif_jpg")],
        [InlineKeyboardButton("🖼 GIF to JPEG", callback_data="convert_img_gif_jpeg")],
        [InlineKeyboardButton("🖼 GIF to BMP", callback_data="convert_img_gif_bmp")],
        
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_audio_conversion_keyboard():
    """Get audio conversion options - ALL 6 COMBINATIONS"""
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
    """Get video conversion options - ALL 12 COMBINATIONS"""
    keyboard = [
        # MP4 conversions
        [InlineKeyboardButton("🎥 MP4 to AVI", callback_data="convert_video_mp4_avi")],
        [InlineKeyboardButton("🎥 MP4 to MOV", callback_data="convert_video_mp4_mov")],
        [InlineKeyboardButton("🎥 MP4 to MKV", callback_data="convert_video_mp4_mkv")],
        [InlineKeyboardButton("🎥 MP4 to GIF", callback_data="convert_video_mp4_gif")],
        
        # AVI conversions
        [InlineKeyboardButton("🎥 AVI to MP4", callback_data="convert_video_avi_mp4")],
        [InlineKeyboardButton("🎥 AVI to MOV", callback_data="convert_video_avi_mov")],
        [InlineKeyboardButton("🎥 AVI to MKV", callback_data="convert_video_avi_mkv")],
        
        # MOV conversions
        [InlineKeyboardButton("🎥 MOV to MP4", callback_data="convert_video_mov_mp4")],
        [InlineKeyboardButton("🎥 MOV to AVI", callback_data="convert_video_mov_avi")],
        [InlineKeyboardButton("🎥 MOV to MKV", callback_data="convert_video_mov_mkv")],
        
        # MKV conversions
        [InlineKeyboardButton("🎥 MKV to MP4", callback_data="convert_video_mkv_mp4")],
        [InlineKeyboardButton("🎥 MKV to AVI", callback_data="convert_video_mkv_avi")],
        [InlineKeyboardButton("🎥 MKV to MOV", callback_data="convert_video_mkv_mov")],
        
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_presentation_conversion_keyboard():
    """Get presentation conversion options - ALL 3 CONVERSIONS"""
    keyboard = [
        [InlineKeyboardButton("🖼 PPTX to PDF", callback_data="convert_presentation_pptx_pdf")],
        [InlineKeyboardButton("🖼 PPT to PDF", callback_data="convert_presentation_ppt_pdf")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_format_suggestions_keyboard(file_extension, file_type):
    """Get smart conversion suggestions for a file type"""
    keyboard = []
    
    # Get supported conversions from router
    try:
        # Run the async function in a sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        supported_formats = loop.run_until_complete(
            converter_router.get_supported_conversions(file_extension)
        )
        loop.close()
    except Exception as e:
        logger.error(f"Error getting supported conversions: {e}")
        # Fallback if async call fails
        supported_formats = get_fallback_suggestions(file_extension, file_type)
    
    # Create buttons for each supported conversion
    row = []
    for i, target_format in enumerate(supported_formats):
        if target_format != file_extension:  # Don't suggest converting to same format
            # Use emojis based on target format type
            emoji = _get_format_emoji(target_format)
            button = InlineKeyboardButton(
                f"{emoji} {target_format.upper()}",
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
    keyboard.append([InlineKeyboardButton("🔍 Browse All Categories", callback_data="commands")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def _get_format_emoji(format_type):
    """Get appropriate emoji for file format"""
    emoji_map = {
        'pdf': '📄',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🎬', 'bmp': '🖼️',
        'mp3': '🎵', 'wav': '🎵', 'aac': '🎵',
        'mp4': '🎥', 'avi': '🎥', 'mov': '🎥', 'mkv': '🎥',
        'docx': '📝', 'txt': '📝', 'xlsx': '📊', 'odt': '📝',
        'pptx': '🖼️', 'ppt': '🖼️'
    }
    return emoji_map.get(format_type, '📁')

def get_fallback_suggestions(file_extension, file_type):
    """Fallback suggestions if router fails"""
    suggestions_map = {
        'image': ['jpg', 'png', 'pdf', 'bmp', 'gif'],
        'audio': ['mp3', 'wav', 'aac'],
        'video': ['mp4', 'avi', 'mov', 'mkv', 'gif'],
        'document': ['pdf', 'docx', 'txt', 'xlsx'],
        'presentation': ['pdf']
    }
    
    # Remove current format from suggestions
    file_extension = file_extension.lower()
    suggestions = suggestions_map.get(file_type, [])
    return [fmt for fmt in suggestions if fmt != file_extension][:8]  # Limit to 8 suggestions

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

# ========== PERSISTENT MENU KEYBOARDS ==========

def get_persistent_menu_keyboard():
    """Get persistent menu that appears after conversions"""
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Another File", callback_data="convert_another")],
        [InlineKeyboardButton("📁 Browse Categories", callback_data="commands")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        [InlineKeyboardButton("📊 History", callback_data="history")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_conversion_complete_keyboard():
    """Keyboard shown after successful conversion"""
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Another File", callback_data="convert_another")],
        [InlineKeyboardButton("📁 Upload New File", callback_data="convert_file")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_upload_prompt_keyboard():
    """Keyboard shown when prompting for file upload"""
    keyboard = [
        [InlineKeyboardButton("📁 Upload File", callback_data="convert_file")],
        [InlineKeyboardButton("🔙 Back to Categories", callback_data="commands")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_after_upload_keyboard():
    """Keyboard shown after file upload with conversion options"""
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Another", callback_data="convert_another")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)