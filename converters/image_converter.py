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
        """Convert image to different format with comprehensive format support"""
        try:
            # Handle special formats first
            if output_format.lower() in ['heic', 'avif']:
                return await self._convert_with_ffmpeg(input_path, output_format)
            elif output_format.lower() == 'svg':
                return await self._rasterize_svg(input_path, 'png')  # SVG to raster
            elif input_path.lower().endswith('.svg'):
                return await self._rasterize_svg(input_path, output_format)
            elif output_format.lower() in ['eps', 'psd']:
                return await self._convert_special_formats(input_path, output_format)
            else:
                return await self._convert_with_pillow(input_path, output_format, quality)
                
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            raise Exception(f"Image conversion failed: {str(e)}")
    
    async def _convert_with_pillow(self, input_path, output_format, quality=95):
        """Convert using Pillow for common formats"""
        try:
            with Image.open(input_path) as img:
                # Handle multi-frame images (GIF, APNG)
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
                    save_kwargs = {'format': 'JPEG', 'quality': quality, 'optimize': True, 'progressive': True}
                elif output_format.lower() == 'webp':
                    save_kwargs = {'format': 'WEBP', 'quality': quality, 'method': 6}
                elif output_format.lower() == 'png':
                    save_kwargs = {'format': 'PNG', 'optimize': True}
                elif output_format.lower() == 'tiff':
                    save_kwargs = {'format': 'TIFF', 'compression': 'tiff_lzw'}
                elif output_format.lower() == 'bmp':
                    save_kwargs = {'format': 'BMP'}
                elif output_format.lower() == 'ico':
                    save_kwargs = {'format': 'ICO', 'sizes': [(32, 32), (64, 64)]}
                else:
                    save_kwargs = {'format': output_format.upper()}
                
                img.save(output_path, **save_kwargs)
                return output_path
                
        except Exception as e:
            raise Exception(f"Pillow conversion error: {str(e)}")
    
    async def _convert_with_ffmpeg(self, input_path, output_format):
        """Convert using FFmpeg for formats not supported by Pillow"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-y',  # Overwrite output
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
            
            # Use cairosvg if available, otherwise fallback
            try:
                import cairosvg
                if output_format == 'png':
                    cairosvg.svg2png(url=input_path, write_to=output_path)
                elif output_format in ['jpg', 'jpeg']:
                    cairosvg.svg2png(url=input_path, write_to=output_path)
                    # Convert PNG to JPG
                    with Image.open(output_path) as img:
                        img = img.convert('RGB')
                        img.save(output_path.replace('.png', '.jpg'), 'JPEG', quality=95)
                        output_path = output_path.replace('.png', '.jpg')
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
                    raise Exception("SVG conversion failed - no tools available")
                    
        except Exception as e:
            raise Exception(f"SVG conversion failed: {str(e)}")
    
    async def _convert_animated_image(self, input_path, output_format):
        """Convert animated images (GIF, APNG)"""
        try:
            if output_format.lower() == 'gif':
                # Simple copy for GIF to GIF
                output_path = input_path.rsplit('.', 1)[0] + '.gif'
                import shutil
                shutil.copy2(input_path, output_path)
                return output_path
            else:
                # Convert animated image to first frame
                with Image.open(input_path) as img:
                    img.seek(0)  # Get first frame
                    output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
                    img.save(output_path)
                    return output_path
                    
        except Exception as e:
            raise Exception(f"Animated image conversion failed: {str(e)}")
    
    async def _convert_special_formats(self, input_path, output_format):
        """Convert special formats like EPS, PSD"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # Use ImageMagick for special formats
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
                raise Exception(f"Special format conversion failed")
                
        except Exception as e:
            raise Exception(f"Special format conversion error: {str(e)}")
    
    async def compress_image(self, input_path, quality=85):
        """Compress image by reducing quality"""
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
        """Resize image with high quality"""
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
                        raise Exception("Please specify both width and height for non-ratio resize")
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                output_path = input_path.rsplit('.', 1)[0] + f'_resized_{new_width}x{new_height}.' + input_path.rsplit('.', 1)[1]
                img.save(output_path, optimize=True)
                return output_path
        except Exception as e:
            raise Exception(f"Image resize failed: {str(e)}")

# Global converter instance - FIXED: Remove circular import
img_converter = ImageConverter()