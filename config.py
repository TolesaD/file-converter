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
    
    # Complete supported formats
    SUPPORTED_FORMATS = {
        'image': [
            'png', 'jpg', 'jpeg', 'jp2', 'webp', 'bmp', 'tif', 'tiff', 
            'gif', 'ico', 'heic', 'avif', 'tgs', 'psd', 'svg', 'apng', 
            'eps', 'raw', 'dng', 'cr2'
        ],
        'audio': [
            'mp3', 'ogg', 'opus', 'wav', 'flac', 'wma', 'oga', 'm4a', 
            'aac', 'aiff', 'amr', 'ape', 'mid'
        ],
        'video': [
            'mp4', 'avi', 'wmv', 'mkv', '3gp', '3gpp', 'mpg', 'mpeg', 
            'webm', 'ts', 'mov', 'flv', 'asf', 'vob', 'm4v', 'rmvb'
        ],
        'document': [
            'xlsx', 'xls', 'txt', 'rtf', 'doc', 'docx', 'odt', 'pdf', 
            'ods', 'torrent', 'csv', 'html'
        ],
        'presentation': [
            'ppt', 'pptx', 'pptm', 'pps', 'ppsx', 'ppsm', 'pot', 'potx', 
            'potm', 'odp', 'sxp', 'key'
        ]
    }
    
    # Format categories with emojis
    FORMAT_CATEGORIES = {
        'image': '📷 Images',
        'audio': '🔊 Audio', 
        'video': '📹 Video',
        'document': '💼 Documents',
        'presentation': '🖼 Presentations'
    }

# Create directories
os.makedirs(Config.TEMP_DIR, exist_ok=True)
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)