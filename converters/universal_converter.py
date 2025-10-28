import os
import asyncio
import subprocess
import tempfile
from pathlib import Path
import logging
from config import Config

logger = logging.getLogger(__name__)

class UniversalConverter:
    def __init__(self):
        self.supported_formats = {}
        for category, formats in Config.SUPPORTED_FORMATS.items():
            for fmt in formats:
                self.supported_formats[fmt] = category
    
    async def _check_ffmpeg_available(self):
        """Check if FFmpeg is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def convert_file(self, input_path, output_format, input_extension=None):
        """Universal file conversion that handles ALL 72+ formats"""
        try:
            if not input_extension:
                input_extension = os.path.splitext(input_path)[1].lstrip('.').lower()
            
            logger.info(f"Converting {input_extension} to {output_format}")
            
            # Get file categories
            input_category = self.supported_formats.get(input_extension)
            output_category = self.supported_formats.get(output_format)
            
            if not input_category:
                raise Exception(f"Unsupported input format: {input_extension}")
            if not output_category:
                raise Exception(f"Unsupported output format: {output_format}")
            
            # Route to appropriate converter
            if input_category == 'image':
                return await self._convert_image(input_path, output_format, input_extension)
            elif input_category == 'audio':
                return await self._convert_audio(input_path, output_format, input_extension)
            elif input_category == 'video':
                return await self._convert_video(input_path, output_format, input_extension)
            elif input_category == 'document':
                return await self._convert_document(input_path, output_format, input_extension)
            else:
                raise Exception(f"No converter for category: {input_category}")
                
        except Exception as e:
            logger.error(f"Universal conversion error: {e}")
            raise
    
    async def _convert_image(self, input_path, output_format, input_extension):
        """Convert image files"""
        try:
            from PIL import Image
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            with Image.open(input_path) as img:
                # Handle format-specific conversions
                if output_format in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                    # Convert RGBA to RGB for JPEG
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
                
                # Save with appropriate settings
                save_kwargs = {}
                if output_format in ['jpg', 'jpeg']:
                    save_kwargs = {'format': 'JPEG', 'quality': 95, 'optimize': True}
                elif output_format == 'webp':
                    save_kwargs = {'format': 'WEBP', 'quality': 95}
                elif output_format == 'png':
                    save_kwargs = {'format': 'PNG', 'optimize': True}
                else:
                    save_kwargs = {'format': output_format.upper()}
                
                img.save(output_path, **save_kwargs)
                return output_path
                
        except Exception as e:
            # Fallback to FFmpeg for difficult formats
            return await self._convert_with_ffmpeg(input_path, output_format)
    
    async def _convert_audio(self, input_path, output_format, input_extension):
        """Convert audio files using FFmpeg"""
        try:
            # Check FFmpeg availability
            if not await self._check_ffmpeg_available():
                raise Exception("FFmpeg is required for audio conversion but is not installed")
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-y',  # Overwrite
                '-loglevel', 'error',
                '-hide_banner',
            ]
            
            # Audio codec settings
            if output_format == 'mp3':
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '192k'])
            elif output_format == 'wav':
                cmd.extend(['-codec:a', 'pcm_s16le'])
            elif output_format == 'flac':
                cmd.extend(['-codec:a', 'flac'])
            elif output_format == 'ogg':
                cmd.extend(['-codec:a', 'libvorbis', '-b:a', '192k'])
            elif output_format in ['m4a', 'aac']:
                cmd.extend(['-codec:a', 'aac', '-b:a', '192k'])
            else:
                cmd.extend(['-codec:a', 'copy'])  # Try to copy without re-encoding
            
            cmd.append(output_path)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Audio conversion failed"
                raise Exception(f"Audio conversion error: {error_msg}")
                
        except Exception as e:
            raise Exception(f"Audio conversion failed: {str(e)}")
    
    async def _convert_video(self, input_path, output_format, input_extension):
        """Convert video files using FFmpeg"""
        try:
            # Check FFmpeg availability
            if not await self._check_ffmpeg_available():
                raise Exception("FFmpeg is required for video conversion but is not installed")
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-y',
                '-loglevel', 'error',
                '-hide_banner',
            ]
            
            # Video conversion settings
            if output_format == 'mp4':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac', '-movflags', '+faststart'])
            elif output_format == 'avi':
                cmd.extend(['-c:v', 'mpeg4', '-c:a', 'mp3'])
            elif output_format == 'mov':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
            elif output_format == 'webm':
                cmd.extend(['-c:v', 'libvpx-vp9', '-c:a', 'libvorbis'])
            elif output_format == 'gif':
                # Convert to GIF
                cmd = [
                    'ffmpeg', '-i', input_path,
                    '-y',
                    '-t', '10',  # 10 seconds max
                    '-vf', 'fps=10,scale=320:-1:flags=lanczos',
                    output_path
                ]
            else:
                cmd.extend(['-c', 'copy'])  # Try direct copy
            
            if output_format != 'gif':  # Already set for GIF
                cmd.append(output_path)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Video conversion failed"
                raise Exception(f"Video conversion error: {error_msg}")
                
        except Exception as e:
            raise Exception(f"Video conversion failed: {str(e)}")
    
    async def _convert_document(self, input_path, output_format, input_extension):
        """Convert document files"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # PDF conversions
            if input_extension == 'pdf':
                if output_format == 'txt':
                    return await self._pdf_to_text(input_path, output_path)
                elif output_format in ['jpg', 'jpeg', 'png']:
                    return await self._pdf_to_image(input_path, output_path, output_format)
                elif output_format == 'html':
                    return await self._pdf_to_html(input_path, output_path)
                elif output_format == 'docx':
                    return await self._pdf_to_docx(input_path, output_path)
            
            # Text conversions
            elif input_extension in ['txt', 'html', 'htm']:
                if output_format == 'pdf':
                    return await self._text_to_pdf(input_path, output_path)
            
            # Office document conversions
            elif input_extension in ['docx', 'doc']:
                if output_format == 'pdf':
                    return await self._docx_to_pdf(input_path, output_path)
                elif output_format == 'txt':
                    return await self._docx_to_text(input_path, output_path)
            
            # Spreadsheet conversions
            elif input_extension in ['xlsx', 'xls', 'csv']:
                if output_format == 'pdf':
                    return await self._excel_to_pdf(input_path, output_path)
            
            # Presentation conversions
            elif input_extension in ['pptx', 'ppt']:
                if output_format == 'pdf':
                    return await self._ppt_to_pdf(input_path, output_path)
            
            # For unsupported conversions, use a generic approach
            raise Exception(f"Document conversion from {input_extension} to {output_format} not implemented")
            
        except Exception as e:
            raise Exception(f"Document conversion failed: {str(e)}")
    
    async def _pdf_to_text(self, input_path, output_path):
        """Convert PDF to text"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(input_path)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_content += text + "\n\n"
            
            doc.close()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to text conversion failed: {str(e)}")
    
    async def _pdf_to_image(self, input_path, output_path, output_format):
        """Convert PDF to image"""
        try:
            from pdf2image import convert_from_path
            
            images = convert_from_path(input_path, dpi=150)
            if images:
                # Save first page only
                images[0].save(output_path, format=output_format.upper(), quality=95)
                return output_path
            else:
                raise Exception("No pages found in PDF")
        except Exception as e:
            raise Exception(f"PDF to image conversion failed: {str(e)}")
    
    async def _pdf_to_html(self, input_path, output_path):
        """Convert PDF to HTML (basic implementation)"""
        try:
            import fitz
            
            doc = fitz.open(input_path)
            html_content = "<html><body>\n"
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                html_content += f"<div style='page-break-after: always;'>\n"
                html_content += f"<h2>Page {page_num + 1}</h2>\n"
                html_content += f"<pre>{text}</pre>\n"
                html_content += "</div>\n"
            
            html_content += "</body></html>"
            doc.close()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to HTML conversion failed: {str(e)}")
    
    async def _pdf_to_docx(self, input_path, output_path):
        """Convert PDF to DOCX"""
        try:
            from pdf2docx import Converter
            
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to DOCX conversion failed: {str(e)}")
    
    async def _text_to_pdf(self, input_path, output_path):
        """Convert text to PDF"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica", 12)
            y_position = height - 40
            line_height = 14
            
            # Simple text wrapping
            lines = []
            for paragraph in text_content.split('\n'):
                words = paragraph.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if c.stringWidth(test_line, "Helvetica", 12) < (width - 100):
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(' '.join(current_line))
                lines.append('')  # Empty line between paragraphs
            
            # Add lines to PDF
            for line in lines[:100]:  # Limit to 100 lines
                if y_position < 40:
                    c.showPage()
                    y_position = height - 40
                    c.setFont("Helvetica", 12)
                
                if line.strip():
                    c.drawString(50, y_position, line)
                y_position -= line_height
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Text to PDF conversion failed: {str(e)}")
    
    async def _docx_to_pdf(self, input_path, output_path):
        """Convert DOCX to PDF"""
        try:
            # Try docx2pdf first
            try:
                from docx2pdf import convert
                convert(input_path, output_path)
                return output_path
            except:
                # Fallback to manual conversion
                from docx import Document
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                
                doc = Document(input_path)
                c = canvas.Canvas(output_path, pagesize=letter)
                width, height = letter
                
                c.setFont("Helvetica", 12)
                y_position = height - 40
                line_height = 14
                
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        if y_position < 40:
                            c.showPage()
                            y_position = height - 40
                            c.setFont("Helvetica", 12)
                        
                        c.drawString(50, y_position, paragraph.text)
                        y_position -= line_height
                
                c.save()
                return output_path
                
        except Exception as e:
            raise Exception(f"DOCX to PDF conversion failed: {str(e)}")
    
    async def _docx_to_text(self, input_path, output_path):
        """Convert DOCX to text"""
        try:
            from docx import Document
            
            doc = Document(input_path)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_content))
            
            return output_path
        except Exception as e:
            raise Exception(f"DOCX to text conversion failed: {str(e)}")
    
    async def _excel_to_pdf(self, input_path, output_path):
        """Convert Excel to PDF"""
        try:
            import pandas as pd
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            if input_path.endswith('.csv'):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path)
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, f"Data from: {os.path.basename(input_path)}")
            
            c.setFont("Helvetica", 10)
            y_position = height - 80
            
            # Add headers
            headers = df.columns.tolist()
            for i, header in enumerate(headers):
                c.drawString(50 + i * 100, y_position, str(header)[:15])
            
            y_position -= 20
            
            # Add data (first 20 rows)
            for _, row in df.head(20).iterrows():
                for i, value in enumerate(row):
                    c.drawString(50 + i * 100, y_position, str(value)[:15])
                y_position -= 15
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Excel to PDF conversion failed: {str(e)}")
    
    async def _ppt_to_pdf(self, input_path, output_path):
        """Convert PowerPoint to PDF"""
        try:
            from pptx import Presentation
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            prs = Presentation(input_path)
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            for i, slide in enumerate(prs.slides):
                if i > 0:
                    c.showPage()
                
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, f"Slide {i+1}")
                
                y_position = height - 80
                c.setFont("Helvetica", 12)
                
                # Extract text from slide
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        c.drawString(50, y_position, shape.text[:80])
                        y_position -= 20
                        if y_position < 50:
                            c.showPage()
                            y_position = height - 50
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"PowerPoint to PDF conversion failed: {str(e)}")
    
    async def _convert_with_ffmpeg(self, input_path, output_format):
        """Generic FFmpeg conversion fallback with better error handling"""
        try:
            # Check if FFmpeg is available
            if not await self._check_ffmpeg_available():
                raise Exception("FFmpeg is not installed or not available in PATH")
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-y',
                '-loglevel', 'error',
                '-hide_banner',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "FFmpeg conversion failed"
                logger.error(f"FFmpeg error: {error_msg}")
                raise Exception(f"FFmpeg conversion failed: {error_msg}")
                
        except asyncio.TimeoutError:
            raise Exception("FFmpeg conversion timed out")
        except Exception as e:
            raise Exception(f"FFmpeg conversion failed: {str(e)}")

# Global universal converter instance
universal_converter = UniversalConverter()