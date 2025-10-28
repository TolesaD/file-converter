import os
import asyncio
import logging
from config import Config
from .document_converter import doc_converter
from .image_converter import img_converter
from .audio_converter import audio_converter
from .video_converter import video_converter

logger = logging.getLogger(__name__)

class ConverterRouter:
    def __init__(self):
        self.converters = {
            'image': img_converter,
            'audio': audio_converter, 
            'video': video_converter,
            'document': doc_converter
        }
    
    def get_file_category(self, file_extension):
        """Determine file category from extension"""
        file_extension = file_extension.lower().lstrip('.')
        
        for category, extensions in Config.SUPPORTED_FORMATS.items():
            if file_extension in extensions:
                return category
        return None
    
    async def convert_file(self, input_path, output_format, input_extension=None):
        """Universal file conversion method that handles ALL formats"""
        try:
            if not input_extension:
                input_extension = os.path.splitext(input_path)[1].lstrip('.').lower()
            
            input_category = self.get_file_category(input_extension)
            output_category = self.get_file_category(output_format)
            
            logger.info(f"Converting: {input_extension} ({input_category}) -> {output_format} ({output_category})")
            
            if not input_category:
                raise Exception(f"Unsupported input format: {input_extension}")
            
            if not output_category:
                raise Exception(f"Unsupported output format: {output_format}")
            
            # Special cross-category conversions
            if input_category == 'image' and output_format == 'pdf':
                output_path = input_path.rsplit('.', 1)[0] + '.pdf'
                return await doc_converter.convert_images_to_pdf([input_path], output_path)
            
            elif input_extension == 'pdf' and output_format in ['jpg', 'jpeg', 'png', 'webp']:
                return await doc_converter.convert_pdf_to_image(input_path, output_format)
            
            elif input_category == 'video' and output_category == 'audio':
                return await video_converter.extract_audio(input_path, output_format)
            
            elif input_category == 'video' and output_format == 'gif':
                return await video_converter.create_gif(input_path)
            
            # Route to appropriate converter
            if input_category in self.converters:
                converter = self.converters[input_category]
                
                if hasattr(converter, 'convert_format'):
                    return await converter.convert_format(input_path, output_format)
                elif hasattr(converter, 'convert_document'):
                    return await converter.convert_document(input_path, output_format)
                else:
                    raise Exception(f"Converter for {input_category} doesn't support conversion")
            else:
                raise Exception(f"No converter available for {input_category} files")
                
        except Exception as e:
            logger.error(f"Conversion routing error: {e}")
            raise
    
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
        
        # Add cross-category conversions
        if input_category == 'image':
            supported.append('pdf')  # Images to PDF
        elif input_extension == 'pdf':
            supported.extend(['jpg', 'png', 'docx', 'txt', 'html'])  # PDF to various
        elif input_category == 'video':
            supported.extend(['mp3', 'wav', 'gif'])  # Video to audio/GIF
        
        # Add basic format conversions within same category
        if input_category == 'image':
            basic_image_formats = ['jpg', 'png', 'webp', 'bmp', 'gif']
            supported.extend([fmt for fmt in basic_image_formats if fmt != input_extension])
        elif input_category == 'audio':
            basic_audio_formats = ['mp3', 'wav', 'ogg', 'flac']
            supported.extend([fmt for fmt in basic_audio_formats if fmt != input_extension])
        elif input_category == 'video':
            basic_video_formats = ['mp4', 'avi', 'mov', 'webm']
            supported.extend([fmt for fmt in basic_video_formats if fmt != input_extension])
        elif input_category == 'document':
            basic_doc_formats = ['pdf', 'txt', 'docx', 'html']
            supported.extend([fmt for fmt in basic_doc_formats if fmt != input_extension])
        
        return list(set(supported))[:12]  # Limit to 12 options

# Global router instance
converter_router = ConverterRouter()