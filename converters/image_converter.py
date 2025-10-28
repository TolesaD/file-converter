import os
import asyncio
import logging
import subprocess
from PIL import Image, ImageFilter, ImageEnhance
import aiofiles

logger = logging.getLogger(__name__)

class ImageConverter:
    def __init__(self):
        self.supported_formats = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif', 'ico', 'svg']
    
    async def convert_format(self, input_path: str, output_format: str) -> str:
        """Convert image to different format"""
        try:
            output_path = os.path.splitext(input_path)[0] + f'_converted.{output_format}'
            
            # Handle special formats
            if input_path.lower().endswith('.svg'):
                return await self._convert_svg(input_path, output_path, output_format)
            else:
                return await self._convert_with_pil(input_path, output_path, output_format)
                
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            raise Exception(f"Image to {output_format} conversion failed")
    
    async def _convert_with_pil(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert image using PIL"""
        try:
            with Image.open(input_path) as img:
                # Handle transparency for JPEG
                if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB' and output_format.lower() in ['jpg', 'jpeg', 'webp']:
                    img = img.convert('RGB')
                
                # Save with optimization
                save_kwargs = {'optimize': True}
                if output_format.lower() in ['jpg', 'jpeg', 'webp']:
                    save_kwargs['quality'] = 85
                
                img.save(output_path, **save_kwargs)
                return output_path
                
        except Exception as e:
            logger.error(f"PIL conversion error: {e}")
            # Fallback to ImageMagick
            return await self._convert_with_imagemagick(input_path, output_path)
    
    async def _convert_svg(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert SVG to raster"""
        try:
            import cairosvg
            cairosvg.svg2png(url=input_path, write_to=output_path)
            
            # If target format is not PNG, convert again
            if output_format.lower() != 'png':
                intermediate_path = output_path
                output_path = os.path.splitext(output_path)[0] + f'.{output_format}'
                await self._convert_with_pil(intermediate_path, output_path, output_format)
                os.remove(intermediate_path)
            
            return output_path
        except ImportError:
            # Use ImageMagick as fallback
            return await self._convert_with_imagemagick(input_path, output_path)
    
    async def _convert_with_imagemagick(self, input_path: str, output_path: str) -> str:
        """Convert using ImageMagick as fallback"""
        try:
            cmd = ['convert', input_path, output_path]
            await self._run_command(cmd)
            return output_path
        except Exception as e:
            logger.error(f"ImageMagick conversion error: {e}")
            raise Exception("Image conversion failed - no available converters")
    
    async def apply_filter(self, input_path: str, filter_type: str) -> str:
        """Apply image filters"""
        try:
            output_path = os.path.splitext(input_path)[0] + f'_{filter_type}.jpg'
            
            with Image.open(input_path) as img:
                if filter_type == 'blur':
                    filtered = img.filter(ImageFilter.BLUR)
                elif filter_type == 'sharpen':
                    filtered = img.filter(ImageFilter.SHARPEN)
                elif filter_type == 'grayscale':
                    filtered = img.convert('L')
                elif filter_type == 'emboss':
                    filtered = img.filter(ImageFilter.EMBOSS)
                elif filter_type == 'contour':
                    filtered = img.filter(ImageFilter.CONTOUR)
                elif filter_type == 'invert':
                    if img.mode == 'RGBA':
                        r, g, b, a = img.split()
                        r = Image.eval(r, lambda x: 255 - x)
                        g = Image.eval(g, lambda x: 255 - x)
                        b = Image.eval(b, lambda x: 255 - x)
                        filtered = Image.merge('RGBA', (r, g, b, a))
                    else:
                        filtered = Image.eval(img, lambda x: 255 - x)
                else:
                    raise Exception(f"Unknown filter: {filter_type}")
                
                filtered.save(output_path, 'JPEG', quality=85)
                return output_path
                
        except Exception as e:
            logger.error(f"Filter application error: {e}")
            raise Exception(f"Failed to apply {filter_type} filter")
    
    async def compress_image(self, input_path: str, quality: int = 75) -> str:
        """Compress image"""
        output_path = os.path.splitext(input_path)[0] + '_compressed.jpg'
        
        with Image.open(input_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, 'JPEG', optimize=True, quality=quality)
        
        return output_path
    
    async def resize_image(self, input_path: str, width: int = None, height: int = None) -> str:
        """Resize image"""
        output_path = os.path.splitext(input_path)[0] + '_resized.jpg'
        
        with Image.open(input_path) as img:
            if width and height:
                new_size = (width, height)
            elif width:
                ratio = width / img.width
                new_size = (width, int(img.height * ratio))
            elif height:
                ratio = height / img.height
                new_size = (int(img.width * ratio), height)
            else:
                raise Exception("Either width or height must be specified")
            
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            resized.save(output_path, 'JPEG', quality=85)
        
        return output_path
    
    async def _run_command(self, cmd: list) -> str:
        """Run system command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"Command failed: {error_msg}")
            
            return stdout.decode() if stdout else ""
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise Exception(f"Conversion failed: {str(e)}")

# Global instance
img_converter = ImageConverter()