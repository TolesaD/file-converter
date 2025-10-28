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
    
    # Simplified supported formats
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
    
    # Conversion mapping - what can be converted to what
    CONVERSION_MAP = {
        'image': {
            'png': ['jpg', 'jpeg', 'bmp', 'gif', 'pdf'],
            'jpg': ['png', 'bmp', 'gif', 'pdf'],
            'jpeg': ['png', 'bmp', 'gif', 'pdf'],
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
            'pdf': ['docx', 'txt'],
            'docx': ['pdf', 'txt'],
            'txt': ['pdf', 'docx'],
            'xlsx': ['pdf'],
            'odt': ['pdf', 'docx']
        },
        'presentation': {
            'pptx': ['pdf'],
            'ppt': ['pdf']
        }
    }

# Create directories
os.makedirs(Config.TEMP_DIR, exist_ok=True)
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)