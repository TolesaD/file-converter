import os
import asyncio
import subprocess
from PIL import Image, ImageFilter, ImageOps, ImageSequence
import logging

logger = logging.getLogger(__name__)

class ImageConverter:
    def __init__(self):
        self.supported_formats = [
            'png', 'jpg', 'jpeg', 'jp2', 'webp', 'bmp', 'tif', 'tiff', 
            'gif', 'ico', 'heic', 'avif', 'tgs', 'psd', 'svg', 'apng', 
            'eps', 'raw', 'dng', 'cr2', 'nef', 'arw', 'sr2', 'orf'
        ]
    
    async def convert_format(self, input_path, output_format, quality=95):
        """Convert image to different format"""
        try:
            # Handle special formats with FFmpeg
            if output_format.lower() in ['heic', 'avif']:
                return await self._convert_with_ffmpeg(input_path, output_format)
            elif output_format.lower() == 'svg':
                # SVG output not supported for raster images
                raise Exception("Cannot convert to SVG from raster images")
            elif input_path.lower().endswith('.svg'):
                # Convert SVG to raster
                return await self._rasterize_svg(input_path, output_format)
            else:
                return await self._convert_with_pillow(input_path, output_format, quality)
                
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            raise Exception(f"Image conversion failed: {str(e)}")
    
    async def _convert_with_pillow(self, input_path, output_format, quality=95):
        """Convert using Pillow"""
        try:
            with Image.open(input_path) as img:
                # Handle multi-frame images
                if getattr(img, 'is_animated', False):
                    return await self._convert_animated_image(input_path, output_format)
                
                # Convert to RGB if necessary for JPEG
                if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                    if img.mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode == 'P':
                    img = img.convert('RGB')
                
                output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
                
                # Format-specific settings
                save_kwargs = {}
                if output_format.lower() in ['jpg', 'jpeg']:
                    save_kwargs = {'format': 'JPEG', 'quality': quality, 'optimize': True}
                elif output_format.lower() == 'webp':
                    save_kwargs = {'format': 'WEBP', 'quality': quality}
                elif output_format.lower() == 'png':
                    save_kwargs = {'format': 'PNG', 'optimize': True}
                elif output_format.lower() == 'tiff':
                    save_kwargs = {'format': 'TIFF', 'compression': 'tiff_lzw'}
                elif output_format.lower() == 'bmp':
                    save_kwargs = {'format': 'BMP'}
                elif output_format.lower() == 'ico':
                    # Resize for icon
                    img = img.resize((64, 64), Image.Resampling.LANCZOS)
                    save_kwargs = {'format': 'ICO'}
                else:
                    save_kwargs = {'format': output_format.upper()}
                
                img.save(output_path, **save_kwargs)
                return output_path
                
        except Exception as e:
            raise Exception(f"Pillow conversion error: {str(e)}")
    
    async def _convert_with_ffmpeg(self, input_path, output_format):
        """Convert using FFmpeg for difficult formats"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-y',
                '-loglevel', 'error',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                error_msg = stderr.decode() if stderr else "FFmpeg conversion failed"
                raise Exception(f"FFmpeg error: {error_msg}")
                
        except asyncio.TimeoutError:
            raise Exception("FFmpeg conversion timeout")
        except Exception as e:
            raise Exception(f"FFmpeg conversion error: {str(e)}")
    
    async def _rasterize_svg(self, input_path, output_format):
        """Convert SVG to raster format"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Use cairosvg if available
            try:
                import cairosvg
                
                if output_format == 'png':
                    cairosvg.svg2png(url=input_path, write_to=output_path)
                elif output_format in ['jpg', 'jpeg']:
                    # Convert to PNG first, then to JPG
                    png_path = output_path.replace(f'.{output_format}', '.png')
                    cairosvg.svg2png(url=input_path, write_to=png_path)
                    with Image.open(png_path) as img:
                        img = img.convert('RGB')
                        img.save(output_path, 'JPEG', quality=95)
                    os.remove(png_path)
                else:
                    cairosvg.svg2png(url=input_path, write_to=output_path)
                
                return output_path
            except ImportError:
                # Fallback to ImageMagick
                cmd = ['convert', input_path, output_path]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(process.communicate(), timeout=30)
                
                if os.path.exists(output_path):
                    return output_path
                else:
                    raise Exception("SVG conversion failed")
                    
        except Exception as e:
            raise Exception(f"SVG conversion failed: {str(e)}")
    
    async def _convert_animated_image(self, input_path, output_format):
        """Convert animated images"""
        try:
            if output_format.lower() == 'gif':
                # Keep as GIF
                output_path = input_path.rsplit('.', 1)[0] + '.gif'
                import shutil
                shutil.copy2(input_path, output_path)
                return output_path
            else:
                # Convert to first frame only
                with Image.open(input_path) as img:
                    img.seek(0)
                    output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
                    
                    if output_format in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    img.save(output_path)
                    return output_path
                    
        except Exception as e:
            raise Exception(f"Animated image conversion failed: {str(e)}")
    
    async def compress_image(self, input_path, quality=85):
        """Compress image"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + '_compressed.' + input_path.rsplit('.', 1)[1]
            
            with Image.open(input_path) as img:
                if input_path.lower().endswith(('.png', '.bmp', '.tiff')):
                    # Convert to JPEG for better compression
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    output_path = output_path.rsplit('.', 1)[0] + '.jpg'
                    img.save(output_path, format='JPEG', quality=quality, optimize=True)
                else:
                    img.save(output_path, quality=quality, optimize=True)
            
            return output_path
        except Exception as e:
            raise Exception(f"Image compression failed: {str(e)}")
    
    async def resize_image(self, input_path, width=None, height=None, maintain_ratio=True):
        """Resize image"""
        try:
            with Image.open(input_path) as img:
                original_width, original_height = img.size
                
                if maintain_ratio:
                    if width and height:
                        ratio = min(width/original_width, height/original_height)
                        new_width = int(original_width * ratio)
                        new_height = int(original_height * ratio)
                    elif width:
                        ratio = width / original_width
                        new_width = width
                        new_height = int(original_height * ratio)
                    elif height:
                        ratio = height / original_height
                        new_width = int(original_width * ratio)
                        new_height = height
                    else:
                        raise Exception("Please specify width or height")
                else:
                    if width and height:
                        new_width = width
                        new_height = height
                    else:
                        raise Exception("Please specify both width and height")
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                output_path = input_path.rsplit('.', 1)[0] + f'_resized.{input_path.rsplit(".", 1)[1]}'
                img.save(output_path, optimize=True)
                return output_path
        except Exception as e:
            raise Exception(f"Image resize failed: {str(e)}")
    
    async def apply_filter(self, input_path, filter_type):
        """Apply filter to image"""
        try:
            with Image.open(input_path) as img:
                filters = {
                    'blur': ImageFilter.GaussianBlur(2),
                    'sharpen': ImageFilter.SHARPEN,
                    'contour': ImageFilter.CONTOUR,
                    'emboss': ImageFilter.EMBOSS,
                    'smooth': ImageFilter.SMOOTH,
                }
                
                if filter_type == 'grayscale':
                    img = ImageOps.grayscale(img)
                elif filter_type == 'invert':
                    img = ImageOps.invert(img)
                elif filter_type in filters:
                    img = img.filter(filters[filter_type])
                
                output_path = input_path.rsplit('.', 1)[0] + f'_{filter_type}.{input_path.rsplit(".", 1)[1]}'
                img.save(output_path, optimize=True)
                return output_path
        except Exception as e:
            raise Exception(f"Filter application failed: {str(e)}")

# Global converter instance
img_converter = ImageConverter()