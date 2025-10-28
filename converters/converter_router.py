import os
import asyncio
import logging
from config import Config
from .universal_converter import universal_converter

logger = logging.getLogger(__name__)

class ConverterRouter:
    def __init__(self):
        self.universal_converter = universal_converter
    
    def get_file_category(self, file_extension):
        """Determine file category from extension"""
        file_extension = file_extension.lower().lstrip('.')
        
        for category, extensions in Config.SUPPORTED_FORMATS.items():
            if file_extension in extensions:
                return category
        return None
    
    async def convert_file(self, input_path, output_format, input_extension=None):
        """Universal file conversion method using the universal converter"""
        try:
            if not input_extension:
                input_extension = os.path.splitext(input_path)[1].lstrip('.').lower()
            
            logger.info(f"Routing conversion: {input_extension} -> {output_format}")
            
            # Use the universal converter for ALL conversions
            return await self.universal_converter.convert_file(input_path, output_format, input_extension)
                
        except Exception as e:
            logger.error(f"Conversion routing error: {e}")
            raise
    
    async def get_supported_conversions(self, input_extension):
        """Get all supported output formats for an input format"""
        input_category = self.get_file_category(input_extension)
        
        if not input_category:
            return []
        
        supported = []
        
        # Get all formats that can be converted to
        for output_format in self.universal_converter.supported_formats.keys():
            if output_format != input_extension:
                # For now, assume all formats can be converted to each other within reason
                # In a production system, you'd have more specific rules
                if input_category == 'image' and self.get_file_category(output_format) == 'image':
                    supported.append(output_format)
                elif input_category == 'audio' and self.get_file_category(output_format) == 'audio':
                    supported.append(output_format)
                elif input_category == 'video' and self.get_file_category(output_format) == 'video':
                    supported.append(output_format)
                elif input_category == 'document' and self.get_file_category(output_format) == 'document':
                    supported.append(output_format)
        
        # Add cross-category conversions
        if input_category == 'image':
            supported.append('pdf')
        elif input_extension == 'pdf':
            supported.extend(['jpg', 'png', 'txt', 'docx', 'html'])
        elif input_category == 'video':
            supported.extend(['mp3', 'gif'])
        
        return list(set(supported))[:12]  # Limit to 12 options

# Global router instance
converter_router = ConverterRouter()