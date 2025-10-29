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
        """Universal file conversion for all supported formats"""
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
            elif input_category == 'presentation':
                return await self._convert_presentation(input_path, output_format, input_extension)
            else:
                raise Exception(f"No converter for category: {input_category}")
                
        except Exception as e:
            logger.error(f"Universal conversion error: {e}")
            raise
    
    async def _convert_image(self, input_path, output_format, input_extension):
        """Convert image files - ALL 20 COMBINATIONS SUPPORTED"""
        try:
            from PIL import Image
            
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            with Image.open(input_path) as img:
                # Handle format-specific conversions
                if output_format in ['jpg', 'jpeg']:
                    # Convert to RGB for JPEG formats
                    if img.mode in ('RGBA', 'LA', 'P'):
                        if img.mode == 'P' and 'transparency' in img.info:
                            img = img.convert('RGBA')
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                
                # Handle GIF output
                elif output_format == 'gif':
                    if img.mode != 'P' and hasattr(img, 'is_animated') and not img.is_animated:
                        # Convert single image to GIF
                        img = img.convert('P')
                
                # Save with appropriate settings
                save_kwargs = {}
                if output_format in ['jpg', 'jpeg']:
                    save_kwargs = {'format': 'JPEG', 'quality': 95, 'optimize': True}
                elif output_format == 'png':
                    save_kwargs = {'format': 'PNG', 'optimize': True}
                elif output_format == 'bmp':
                    save_kwargs = {'format': 'BMP'}
                elif output_format == 'gif':
                    save_kwargs = {'format': 'GIF'}
                elif output_format == 'pdf':
                    # Convert image to PDF
                    return await self._image_to_pdf(input_path, output_path)
                else:
                    save_kwargs = {'format': output_format.upper()}
                
                if output_format != 'pdf':  # PDF handled separately
                    img.save(output_path, **save_kwargs)
                    return output_path
                
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            raise Exception(f"Image conversion failed: {str(e)}")
    
    async def _image_to_pdf(self, input_path, output_path):
        """Convert image to PDF"""
        try:
            from PIL import Image
            import img2pdf
            
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as PDF
                with open(output_path, "wb") as f:
                    f.write(img2pdf.convert([input_path]))
            return output_path
        except Exception as e:
            raise Exception(f"Image to PDF conversion failed: {str(e)}")
    
    async def _convert_audio(self, input_path, output_format, input_extension):
        """Convert audio files using FFmpeg - ALL 6 COMBINATIONS SUPPORTED"""
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
            
            # Audio codec settings for all formats
            if output_format == 'mp3':
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '192k'])
            elif output_format == 'wav':
                cmd.extend(['-codec:a', 'pcm_s16le'])
            elif output_format == 'aac':
                cmd.extend(['-codec:a', 'aac', '-b:a', '192k'])
            
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
        """Convert video files using FFmpeg - ALL 12 COMBINATIONS SUPPORTED"""
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
            
            # Video conversion settings for all formats
            if output_format == 'mp4':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac', '-movflags', '+faststart'])
            elif output_format == 'avi':
                cmd.extend(['-c:v', 'mpeg4', '-c:a', 'mp3'])
            elif output_format == 'mov':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
            elif output_format == 'mkv':
                cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
            elif output_format == 'gif':
                # Convert to GIF
                cmd = [
                    'ffmpeg', '-i', input_path,
                    '-y',
                    '-t', '10',  # 10 seconds max
                    '-vf', 'fps=10,scale=320:-1:flags=lanczos',
                    output_path
                ]
            
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
        """Convert document files - ALL RELIABLE COMBINATIONS SUPPORTED"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            # PDF conversions
            if input_extension == 'pdf':
                if output_format == 'txt':
                    return await self._pdf_to_text(input_path, output_path)
                elif output_format in ['jpg', 'jpeg', 'png']:
                    return await self._pdf_to_image(input_path, output_path, output_format)
                elif output_format == 'docx':
                    return await self._pdf_to_docx(input_path, output_path)
                elif output_format == 'xlsx':
                    return await self._pdf_to_excel(input_path, output_path)
            
            # Text conversions
            elif input_extension == 'txt':
                if output_format == 'pdf':
                    return await self._text_to_pdf(input_path, output_path)
                elif output_format == 'docx':
                    return await self._text_to_docx(input_path, output_path)
            
            # Word document conversions
            elif input_extension == 'docx':
                if output_format == 'pdf':
                    return await self._docx_to_pdf(input_path, output_path)
                elif output_format == 'txt':
                    return await self._docx_to_text(input_path, output_path)
            
            # Excel conversions
            elif input_extension == 'xlsx':
                if output_format == 'pdf':
                    return await self._excel_to_pdf(input_path, output_path)
            
            # ODT conversions
            elif input_extension == 'odt':
                if output_format == 'pdf':
                    return await self._odt_to_pdf(input_path, output_path)
            
            raise Exception(f"Document conversion from {input_extension} to {output_format} not implemented")
            
        except Exception as e:
            raise Exception(f"Document conversion failed: {str(e)}")
    
    async def _convert_presentation(self, input_path, output_format, input_extension):
        """Convert presentation files"""
        try:
            output_path = input_path.rsplit('.', 1)[0] + f'.{output_format}'
            
            if output_format == 'pdf':
                if input_extension in ['pptx', 'ppt']:
                    return await self._ppt_to_pdf(input_path, output_path)
            
            raise Exception(f"Presentation conversion from {input_extension} to {output_format} not implemented")
            
        except Exception as e:
            raise Exception(f"Presentation conversion failed: {str(e)}")
    
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
    
    async def _pdf_to_excel(self, input_path, output_path):
        """Convert PDF to Excel (basic text extraction)"""
        try:
            import fitz
            import pandas as pd
            
            doc = fitz.open(input_path)
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    text_content.append([f"Page {page_num + 1}", text[:1000]])  # Limit text length
            
            doc.close()
            
            if text_content:
                df = pd.DataFrame(text_content, columns=['Page', 'Content'])
                df.to_excel(output_path, index=False)
                return output_path
            else:
                raise Exception("No text content found in PDF")
        except Exception as e:
            raise Exception(f"PDF to Excel conversion failed: {str(e)}")
    
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
            lines = text_content.split('\n')
            
            # Add lines to PDF
            for line in lines[:100]:  # Limit to 100 lines
                if y_position < 40:
                    c.showPage()
                    y_position = height - 40
                    c.setFont("Helvetica", 12)
                
                if line.strip():
                    c.drawString(50, y_position, line[:80])
                y_position -= line_height
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Text to PDF conversion failed: {str(e)}")
    
    async def _text_to_docx(self, input_path, output_path):
        """Convert text to DOCX"""
        try:
            from docx import Document
            
            with open(input_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            doc = Document()
            doc.add_paragraph(text_content)
            doc.save(output_path)
            
            return output_path
        except Exception as e:
            raise Exception(f"Text to DOCX conversion failed: {str(e)}")
    
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
                        
                        c.drawString(50, y_position, paragraph.text[:80])
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
    
    async def _odt_to_pdf(self, input_path, output_path):
        """Convert ODT to PDF"""
        try:
            # Use LibreOffice for ODT to PDF conversion
            cmd = [
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path), input_path
            ]
            
            await self._run_command(cmd)
            
            # Find the converted file
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            possible_path = os.path.join(os.path.dirname(output_path), base_name + '.pdf')
            
            if os.path.exists(possible_path):
                if possible_path != output_path:
                    os.rename(possible_path, output_path)
                return output_path
            else:
                raise Exception("ODT to PDF conversion failed")
                
        except Exception as e:
            raise Exception(f"ODT to PDF conversion failed: {str(e)}")
    
    async def _ppt_to_pdf(self, input_path, output_path):
        """Convert PowerPoint to PDF"""
        try:
            # Use LibreOffice for PPT to PDF conversion
            cmd = [
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path), input_path
            ]
            
            await self._run_command(cmd)
            
            # Find the converted file
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            possible_path = os.path.join(os.path.dirname(output_path), base_name + '.pdf')
            
            if os.path.exists(possible_path):
                if possible_path != output_path:
                    os.rename(possible_path, output_path)
                return output_path
            else:
                raise Exception("PowerPoint to PDF conversion failed")
                
        except Exception as e:
            raise Exception(f"PowerPoint to PDF conversion failed: {str(e)}")
    
    async def _run_command(self, cmd):
        """Run system command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Command failed"
                raise Exception(f"Command failed: {error_msg}")
            
            return stdout.decode() if stdout else ""
            
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")

# Global universal converter instance
universal_converter = UniversalConverter()