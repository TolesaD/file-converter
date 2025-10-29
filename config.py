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
    
    # REAL Telegram file size limits (based on actual capabilities)
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB - Telegram's actual limit for bots
    MAX_OUTPUT_SIZE = 2 * 1024 * 1024 * 1024  # 2GB output limit
    
    # Telegram sending limits (much higher than commonly believed)
    MAX_PHOTO_SIZE = 50 * 1024 * 1024  # 50MB for photos (actual limit)
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB for audio files
    MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB for video files
    MAX_DOCUMENT_SIZE = 2 * 1024 * 1024 * 1024  # 2GB for documents
    
    # Directory settings
    TEMP_DIR = "temp"
    UPLOAD_DIR = "temp/uploads"
    OUTPUT_DIR = "temp/outputs"
    
    # Enhanced conversion timeouts for large files
    MAX_CONVERSION_TIME = 1800  # 30 minutes for very large files
    IMAGE_CONVERSION_TIMEOUT = 300  # 5 minutes for images
    AUDIO_CONVERSION_TIMEOUT = 600  # 10 minutes for audio
    VIDEO_CONVERSION_TIMEOUT = 1800  # 30 minutes for video
    DOCUMENT_CONVERSION_TIMEOUT = 600  # 10 minutes for documents
    PRESENTATION_CONVERSION_TIMEOUT = 600  # 10 minutes for presentations
    
    # Queue and processing settings optimized for large files
    MAX_CONCURRENT_JOBS = 2  # Reduce concurrent jobs for large file processing
    JOB_TIMEOUT = 1800  # 30 minutes per job
    
    # Quality settings for large files
    IMAGE_QUALITY = 95
    AUDIO_BITRATE = '320k'
    VIDEO_QUALITY = 'crf=23'
    PDF_DPI = 300
    
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