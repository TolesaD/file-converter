import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Admin User IDs (comma separated)
    ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///converter.db')
    
    # File settings
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB input limit
    MAX_OUTPUT_SIZE = 50 * 1024 * 1024  # 50MB Telegram output limit
    TEMP_DIR = "temp"
    UPLOAD_DIR = "temp/uploads"
    OUTPUT_DIR = "temp/outputs"
    
    # Enhanced conversion timeouts
    MAX_CONVERSION_TIME = 600  # 10 minutes overall
    IMAGE_CONVERSION_TIMEOUT = 180  # 3 minutes for images
    AUDIO_CONVERSION_TIMEOUT = 300  # 5 minutes for audio
    VIDEO_CONVERSION_TIMEOUT = 600  # 10 minutes for video
    DOCUMENT_CONVERSION_TIMEOUT = 300  # 5 minutes for documents
    PRESENTATION_CONVERSION_TIMEOUT = 300  # 5 minutes for presentations
    
    # Queue and processing settings
    MAX_CONCURRENT_JOBS = 3  # Process 3 files simultaneously
    JOB_TIMEOUT = 300  # 5 minutes per job
    
    # Telegram sending limits
    MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB for photos
    MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB for audio
    MAX_VIDEO_SIZE = 20 * 1024 * 1024  # 20MB for video
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB for documents
    
    # Quality settings
    IMAGE_QUALITY = 95  # High quality for images
    AUDIO_BITRATE = '320k'  # High quality for audio
    VIDEO_QUALITY = 'crf=23'  # High quality for video
    PDF_DPI = 300  # High DPI for PDF conversions
    
    # Queue management
    processing_queue = asyncio.Queue()
    active_jobs = 0
    job_lock = asyncio.Lock()
    
    # Complete supported formats
    SUPPORTED_FORMATS = {
        'image': ['png', 'jpg', 'jpeg', 'bmp', 'gif'],
        'audio': ['mp3', 'wav', 'aac'],
        'video': ['mp4', 'avi', 'mov', 'mkv'],
        'document': ['pdf', 'docx', 'txt', 'xlsx', 'odt'],
        'presentation': ['pptx', 'ppt']
    }
    
    # Format categories with emojis
    FORMAT_CATEGORIES = {
        'image': '📷 Images',
        'audio': '🔊 Audio', 
        'video': '📹 Video',
        'document': '💼 Documents',
        'presentation': '🖼 Presentations'
    }
    
    # COMPLETE Conversion mapping - what can be converted to what
    CONVERSION_MAP = {
        'image': {
            'png': ['jpg', 'jpeg', 'bmp', 'gif', 'pdf'],
            'jpg': ['png', 'jpeg', 'bmp', 'gif', 'pdf'],
            'jpeg': ['png', 'jpg', 'bmp', 'gif', 'pdf'],
            'bmp': ['png', 'jpg', 'jpeg', 'gif', 'pdf'],
            'gif': ['png', 'jpg', 'jpeg', 'bmp', 'pdf']
        },
        'audio': {
            'mp3': ['wav', 'aac'],
            'wav': ['mp3', 'aac'],
            'aac': ['mp3', 'wav']
        },
        'video': {
            'mp4': ['avi', 'mov', 'mkv', 'gif'],
            'avi': ['mp4', 'mov', 'mkv'],
            'mov': ['mp4', 'avi', 'mkv'],
            'mkv': ['mp4', 'avi', 'mov']
        },
        'document': {
            'pdf': ['docx', 'txt', 'xlsx'],
            'docx': ['pdf', 'txt'],
            'txt': ['pdf', 'docx'],
            'xlsx': ['pdf'],
            'odt': ['pdf']
        },
        'presentation': {
            'pptx': ['pdf'],
            'ppt': ['pdf']
        }
    }
    
    # Conversion timeouts by category
    @classmethod
    def get_conversion_timeout(cls, category):
        """Get appropriate timeout for conversion category"""
        timeouts = {
            'image': cls.IMAGE_CONVERSION_TIMEOUT,
            'audio': cls.AUDIO_CONVERSION_TIMEOUT,
            'video': cls.VIDEO_CONVERSION_TIMEOUT,
            'document': cls.DOCUMENT_CONVERSION_TIMEOUT,
            'presentation': cls.PRESENTATION_CONVERSION_TIMEOUT
        }
        return timeouts.get(category, cls.MAX_CONVERSION_TIME)
    
    # File size limits by type for Telegram sending
    @classmethod
    def get_telegram_limit(cls, file_type):
        """Get Telegram file size limit for specific file type"""
        limits = {
            'photo': cls.MAX_PHOTO_SIZE,
            'audio': cls.MAX_AUDIO_SIZE,
            'video': cls.MAX_VIDEO_SIZE,
            'document': cls.MAX_DOCUMENT_SIZE
        }
        return limits.get(file_type, cls.MAX_DOCUMENT_SIZE)

# Create directories
os.makedirs(Config.TEMP_DIR, exist_ok=True)
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)