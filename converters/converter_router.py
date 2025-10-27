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
        """Universal file conversion method"""
        try:
            if not input_extension:
                input_extension = os.path.splitext(input_path)[1].lstrip('.').lower()
            
            input_category = self.get_file_category(input_extension)
            output_category = self.get_file_category(output_format)
            
            if not input_category:
                raise Exception(f"Unsupported input format: {input_extension}")
            
            if not output_category:
                raise Exception(f"Unsupported output format: {output_format}")
            
            # Special case: Images to PDF (document conversion)
            if input_category == 'image' and output_format == 'pdf':
                return await doc_converter.convert_images_to_pdf([input_path], 
                    input_path.rsplit('.', 1)[0] + '.pdf')
            
            # Special case: PDF to images (image conversion)
            if input_extension == 'pdf' and output_format in ['jpg', 'jpeg', 'png', 'webp']:
                images = await doc_converter.convert_pdf_to_images(input_path, output_format)
                return images[0] if images else None
            
            # Special case: Video to audio (audio extraction)
            if input_category == 'video' and output_category == 'audio':
                return await video_converter.extract_audio(input_path, output_format)
            
            # Special case: Video to GIF
            if input_category == 'video' and output_format == 'gif':
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
            supported.append('pdf')  # Images can convert to PDF
        elif input_extension == 'pdf':
            supported.extend(['jpg', 'png', 'docx', 'txt'])  # PDF can convert to these
        
        return list(set(supported))  # Remove duplicates

# Global router instance
converter_router = ConverterRouter()