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
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    TEMP_DIR = "temp"
    UPLOAD_DIR = "temp/uploads"
    OUTPUT_DIR = "temp/outputs"
    
    # Queue and processing settings
    MAX_CONCURRENT_JOBS = 3  # Process 3 files simultaneously
    JOB_TIMEOUT = 300  # 5 minutes per job
    
    # Queue management
    processing_queue = asyncio.Queue()
    active_jobs = 0
    job_lock = asyncio.Lock()
    
    # Complete supported formats - 72+ formats
    SUPPORTED_FORMATS = {
        'image': [
            'png', 'jpg', 'jpeg', 'jp2', 'webp', 'bmp', 'tif', 'tiff', 
            'gif', 'ico', 'heic', 'avif', 'tgs', 'psd', 'svg', 'apng', 
            'eps', 'raw', 'dng', 'cr2', 'nef', 'arw', 'sr2', 'orf'
        ],
        'audio': [
            'mp3', 'ogg', 'opus', 'wav', 'flac', 'wma', 'oga', 'm4a', 
            'aac', 'aiff', 'amr', 'ape', 'mid', 'midi', 'aif', 'aifc',
            'au', 'snd', 'ra', 'rm', 'voc', '8svx'
        ],
        'video': [
            'mp4', 'avi', 'wmv', 'mkv', '3gp', '3gpp', 'mpg', 'mpeg', 
            'webm', 'ts', 'mov', 'flv', 'asf', 'vob', 'm4v', 'rmvb',
            'ogv', 'qt', 'm2ts', 'mts', 'f4v', 'mxf', 'divx', 'xvid'
        ],
        'document': [
            'xlsx', 'xls', 'txt', 'rtf', 'doc', 'docx', 'odt', 'pdf', 
            'ods', 'torrent', 'csv', 'html', 'htm', 'md', 'markdown',
            'ppt', 'pptx', 'odp', 'key', 'epub', 'mobi', 'azw3', 'fb2'
        ],
        'archive': [
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso', 'dmg'
        ]
    }
    
    # Format categories with emojis
    FORMAT_CATEGORIES = {
        'image': '📷 Images',
        'audio': '🔊 Audio', 
        'video': '📹 Video',
        'document': '💼 Documents',
        'archive': '📦 Archives'
    }
    
    # Conversion mapping - what can be converted to what
    CONVERSION_MAP = {
        'image': {
            'png': ['jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif', 'ico', 'pdf'],
            'jpg': ['png', 'webp', 'bmp', 'tiff', 'gif', 'ico', 'pdf'],
            'jpeg': ['png', 'webp', 'bmp', 'tiff', 'gif', 'ico', 'pdf'],
            'webp': ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif', 'ico', 'pdf'],
            'bmp': ['png', 'jpg', 'jpeg', 'webp', 'tiff', 'gif', 'ico', 'pdf'],
            'tiff': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif', 'ico', 'pdf'],
            'gif': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'ico', 'pdf'],
            'svg': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'pdf'],
            'ico': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif', 'pdf'],
            'heic': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'pdf'],
            'avif': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'pdf'],
            'psd': ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'pdf']
        },
        'audio': {
            'mp3': ['wav', 'ogg', 'flac', 'm4a', 'aac'],
            'wav': ['mp3', 'ogg', 'flac', 'm4a', 'aac'],
            'ogg': ['mp3', 'wav', 'flac', 'm4a', 'aac'],
            'flac': ['mp3', 'wav', 'ogg', 'm4a', 'aac'],
            'm4a': ['mp3', 'wav', 'ogg', 'flac', 'aac'],
            'aac': ['mp3', 'wav', 'ogg', 'flac', 'm4a']
        },
        'video': {
            'mp4': ['avi', 'mkv', 'webm', 'mov', 'gif'],
            'avi': ['mp4', 'mkv', 'webm', 'mov', 'gif'],
            'mkv': ['mp4', 'avi', 'webm', 'mov', 'gif'],
            'webm': ['mp4', 'avi', 'mkv', 'mov', 'gif'],
            'mov': ['mp4', 'avi', 'mkv', 'webm', 'gif']
        },
        'document': {
            'pdf': ['docx', 'txt', 'html', 'jpg', 'png', 'epub'],
            'docx': ['pdf', 'txt', 'html', 'odt'],
            'txt': ['pdf', 'docx', 'html'],
            'html': ['pdf', 'txt', 'docx'],
            'xlsx': ['pdf', 'csv', 'html'],
            'csv': ['pdf', 'xlsx', 'html'],
            'pptx': ['pdf', 'html'],
            'epub': ['pdf', 'mobi', 'txt']
        }
    }

# Create directories
os.makedirs(Config.TEMP_DIR, exist_ok=True)
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)