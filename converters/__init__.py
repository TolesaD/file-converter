# converters/__init__.py

# Import converter_router first (it has the safe import)
try:
    from .converter_router import converter_router
except ImportError as e:
    print(f"Warning: Could not import converter_router: {e}")
    converter_router = None

# Import universal_converter with error handling
try:
    from .universal_converter import universal_converter
except ImportError as e:
    print(f"Warning: Could not import universal_converter: {e}")
    # Create fallback
    class FallbackUniversalConverter:
        def __init__(self):
            self.supported_formats = {}
        
        async def convert_file(self, input_path, output_format, input_extension=None):
            raise Exception("Universal converter not available")
    
    universal_converter = FallbackUniversalConverter()

# Legacy converters (set to None since you're using universal_converter now)
doc_converter = None
img_converter = None
audio_converter = None
video_converter = None

__all__ = [
    'doc_converter', 
    'img_converter', 
    'audio_converter', 
    'video_converter', 
    'converter_router',
    'universal_converter'
]