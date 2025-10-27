import os
import re
from config import Config

def sanitize_filename(filename):
    """Sanitize filename to remove unsafe characters"""
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(sanitized) > 100:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:95] + ext
    return sanitized

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_file_type_supported(file_extension, file_type):
    """Check if file type is supported for conversion"""
    file_extension = file_extension.lower()
    
    if file_type == 'document':
        supported = Config.SUPPORTED_FORMATS.get('document', [])
    elif file_type == 'image':
        supported = Config.SUPPORTED_FORMATS.get('image', [])
    elif file_type == 'audio':
        supported = Config.SUPPORTED_FORMATS.get('audio', [])
    elif file_type == 'video':
        supported = Config.SUPPORTED_FORMATS.get('video', [])
    else:
        return False
    
    return file_extension in supported

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"