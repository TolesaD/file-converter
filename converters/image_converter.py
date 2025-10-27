import os
from PIL import Image, ImageFilter, ImageOps
import asyncio

class ImageConverter:
    def __init__(self):
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'gif']
    
    async def convert_format(self, input_path, output_format, quality=95):
        """Convert image to different format"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                    if img.mode == 'P':
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
                if output_format.lower() in ['jpg', 'jpeg']:
                    img.save(output_path, format='JPEG', quality=quality, optimize=True, progressive=True)
                elif output_format.lower() == 'webp':
                    img.save(output_path, format='WEBP', quality=quality, method=6)
                elif output_format.lower() == 'png':
                    img.save(output_path, format='PNG', optimize=True)
                else:
                    img.save(output_path, format=output_format.upper())
                
                return output_path
        except Exception as e:
            raise Exception(f"Image format conversion failed: {str(e)}")
    
    async def compress_image(self, input_path, quality=85):
        """Compress image by reducing quality"""
        try:
            with Image.open(input_path) as img:
                output_path = input_path.rsplit('.', 1)[0] + '_compressed.' + input_path.rsplit('.', 1)[1]
                
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
                        # Calculate ratio to fit within dimensions
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
                
                # Use high-quality resampling
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                output_path = input_path.rsplit('.', 1)[0] + f'_resized_{new_width}x{new_height}.' + input_path.rsplit('.', 1)[1]
                img.save(output_path, optimize=True)
                return output_path
        except Exception as e:
            raise Exception(f"Image resize failed: {str(e)}")
    
    async def crop_image(self, input_path, left, top, right, bottom):
        """Crop image to specified coordinates"""
        try:
            with Image.open(input_path) as img:
                # Validate coordinates
                img_width, img_height = img.size
                left = max(0, min(left, img_width))
                top = max(0, min(top, img_height))
                right = max(left, min(right, img_width))
                bottom = max(top, min(bottom, img_height))
                
                cropped_img = img.crop((left, top, right, bottom))
                output_path = input_path.rsplit('.', 1)[0] + '_cropped.' + input_path.rsplit('.', 1)[1]
                cropped_img.save(output_path, optimize=True)
                return output_path
        except Exception as e:
            raise Exception(f"Image crop failed: {str(e)}")
    
    async def apply_filter(self, input_path, filter_type):
        """Apply filter to image"""
        try:
            with Image.open(input_path) as img:
                filters = {
                    'blur': ImageFilter.GaussianBlur(2),
                    'sharpen': ImageFilter.SHARPEN,
                    'contour': ImageFilter.CONTOUR,
                    'detail': ImageFilter.DETAIL,
                    'edge_enhance': ImageFilter.EDGE_ENHANCE,
                    'emboss': ImageFilter.EMBOSS,
                    'smooth': ImageFilter.SMOOTH,
                    'grayscale': 'grayscale',
                    'invert': 'invert'
                }
                
                if filter_type in filters:
                    if filter_type == 'grayscale':
                        img = ImageOps.grayscale(img)
                    elif filter_type == 'invert':
                        img = ImageOps.invert(img)
                    else:
                        img = img.filter(filters[filter_type])
                
                output_path = input_path.rsplit('.', 1)[0] + f'_{filter_type}.' + input_path.rsplit('.', 1)[1]
                img.save(output_path, optimize=True)
                return output_path
        except Exception as e:
            raise Exception(f"Filter application failed: {str(e)}")
    
    async def rotate_image(self, input_path, degrees):
        """Rotate image by specified degrees"""
        try:
            with Image.open(input_path) as img:
                # Expand=True to show entire image after rotation
                rotated_img = img.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC)
                output_path = input_path.rsplit('.', 1)[0] + f'_rotated_{degrees}.' + input_path.rsplit('.', 1)[1]
                rotated_img.save(output_path, optimize=True)
                return output_path
        except Exception as e:
            raise Exception(f"Image rotation failed: {str(e)}")
    
    async def add_watermark(self, input_path, watermark_text, position='center'):
        """Add text watermark to image"""
        try:
            from PIL import ImageDraw, ImageFont
            
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                draw = ImageDraw.Draw(img)
                
                # Try to use a font
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text position
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                img_width, img_height = img.size
                
                positions = {
                    'center': ((img_width - text_width) // 2, (img_height - text_height) // 2),
                    'top_left': (10, 10),
                    'top_right': (img_width - text_width - 10, 10),
                    'bottom_left': (10, img_height - text_height - 10),
                    'bottom_right': (img_width - text_width - 10, img_height - text_height - 10)
                }
                
                x, y = positions.get(position, positions['center'])
                
                # Add semi-transparent background for better visibility
                padding = 5
                draw.rectangle([x-padding, y-padding, x+text_width+padding, y+text_height+padding], 
                             fill=(0, 0, 0, 128))
                
                # Add text
                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255))
                
                output_path = input_path.rsplit('.', 1)[0] + '_watermarked.' + input_path.rsplit('.', 1)[1]
                img.save(output_path, quality=95)
                return output_path
        except Exception as e:
            raise Exception(f"Watermark addition failed: {str(e)}")

# Global converter instance
img_converter = ImageConverter()