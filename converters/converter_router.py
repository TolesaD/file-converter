import os
import asyncio
import logging
from config import Config
from .universal_converter import universal_converter

logger = logging.getLogger(__name__)

class ConverterRouter:
    def __init__(self):
        # Define unsupported formats that don't make sense for conversion
        self.unsupported_formats = [
            'torrent', 'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso', 'dmg',
            'exe', 'app', 'deb', 'rpm', 'msi', 'apk'
        ]
    
    def get_file_category(self, file_extension):
        """Determine file category from extension"""
        file_extension = file_extension.lower().lstrip('.')
        
        # Skip unsupported formats
        if file_extension in self.unsupported_formats:
            return None
            
        for category, extensions in Config.SUPPORTED_FORMATS.items():
            if file_extension in extensions:
                return category
        return None
    
    async def convert_file(self, input_path, output_format, input_extension=None):
        """Universal file conversion method using the universal converter"""
        try:
            if not input_extension:
                input_extension = os.path.splitext(input_path)[1].lstrip('.').lower()
            
            logger.info(f"Router: Converting {input_extension} to {output_format}")
            
            # Check for unsupported formats
            if input_extension in self.unsupported_formats:
                raise Exception(f"{input_extension.upper()} files cannot be converted (unsupported format)")
            
            if output_format in self.unsupported_formats:
                raise Exception(f"Cannot convert to {output_format.upper()} (unsupported format)")
            
            # Verify file exists
            if not os.path.exists(input_path):
                raise Exception(f"Input file not found: {input_path}")
            
            # Get file size and check if it's reasonable
            file_size = os.path.getsize(input_path)
            if file_size > Config.MAX_FILE_SIZE:
                raise Exception(f"File too large: {file_size} bytes (max: {Config.MAX_FILE_SIZE} bytes)")
            
            # Use the universal converter for all conversions
            logger.info(f"Routing to universal converter: {input_extension} -> {output_format}")
            result_path = await universal_converter.convert_file(input_path, output_format, input_extension)
            
            if result_path and os.path.exists(result_path):
                logger.info(f"Conversion successful: {result_path}")
                return result_path
            else:
                raise Exception("Conversion failed - no output file created")
                
        except Exception as e:
            logger.error(f"Conversion routing error: {e}")
            
            # Provide more helpful error messages
            error_msg = str(e).lower()
            if "not implemented" in error_msg:
                raise Exception(f"Conversion from {input_extension.upper()} to {output_format.upper()} is not yet supported")
            elif "unsupported" in error_msg:
                raise Exception(f"Unsupported conversion: {input_extension.upper()} to {output_format.upper()}")
            elif "ffmpeg" in error_msg and "not installed" in error_msg:
                raise Exception("Video/audio conversion requires FFmpeg but it's not available")
            elif "timeout" in error_msg:
                raise Exception("Conversion timed out - file might be too large or complex")
            else:
                raise Exception(f"Conversion failed: {str(e)}")
    
    async def get_supported_conversions(self, input_extension):
        """Get all supported output formats for an input format"""
        input_category = self.get_file_category(input_extension)
        
        if not input_category:
            return []
        
        supported = []
        
        # Get conversions from CONVERSION_MAP
        if input_category in Config.CONVERSION_MAP:
            if input_extension in Config.CONVERSION_MAP[input_category]:
                supported.extend(Config.CONVERSION_MAP[input_category][input_extension])
        
        # Add cross-category conversions based on universal converter capabilities
        if input_category == 'image':
            supported.extend(['pdf', 'jpg', 'png', 'webp', 'bmp'])  # Images to various
        elif input_extension == 'pdf':
            supported.extend(['jpg', 'png', 'docx', 'txt', 'html'])  # PDF to various
        elif input_category == 'video':
            supported.extend(['mp3', 'wav', 'gif', 'mp4', 'avi'])  # Video conversions
        elif input_extension == 'docx':
            supported.extend(['pdf', 'txt'])  # DOCX to PDF/TXT
        elif input_extension in ['xlsx', 'xls']:
            supported.append('pdf')  # Excel to PDF
        elif input_extension in ['pptx', 'ppt']:
            supported.append('pdf')  # PowerPoint to PDF
        
        # Add basic format conversions within same category
        if input_category == 'image':
            basic_image_formats = ['jpg', 'png', 'webp', 'bmp', 'gif', 'tiff', 'jpeg']
            supported.extend([fmt for fmt in basic_image_formats if fmt != input_extension])
        elif input_category == 'audio':
            basic_audio_formats = ['mp3', 'wav', 'ogg', 'flac', 'm4a']
            supported.extend([fmt for fmt in basic_audio_formats if fmt != input_extension])
        elif input_category == 'video':
            basic_video_formats = ['mp4', 'avi', 'mov', 'webm', 'mkv']
            supported.extend([fmt for fmt in basic_video_formats if fmt != input_extension])
        elif input_category == 'document':
            basic_doc_formats = ['pdf', 'txt', 'docx', 'html']
            supported.extend([fmt for fmt in basic_doc_formats if fmt != input_extension])
        
        # Remove unsupported formats and duplicates
        supported = [fmt for fmt in supported if fmt not in self.unsupported_formats]
        supported = list(set(supported))
        
        # Sort by most common formats first
        common_formats = ['pdf', 'jpg', 'png', 'mp3', 'mp4', 'docx', 'txt', 'webp']
        sorted_supported = [fmt for fmt in common_formats if fmt in supported]
        sorted_supported.extend([fmt for fmt in supported if fmt not in common_formats])
        
        return sorted_supported[:15]  # Limit to 15 options

# Global router instance
converter_router = ConverterRouter()