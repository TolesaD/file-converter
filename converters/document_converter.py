import os
import asyncio
import logging
import subprocess
from typing import List
import tempfile
import aiofiles

logger = logging.getLogger(__name__)

class DocumentConverter:
    def __init__(self):
        self.supported_formats = ['pdf', 'docx', 'doc', 'txt', 'html', 'xlsx', 'xls', 'pptx', 'ppt', 'csv', 'odt', 'ods', 'odp']
    
    async def convert_document(self, input_path: str, output_format: str) -> str:
        """Convert document to target format"""
        try:
            input_ext = os.path.splitext(input_path)[1].lower().lstrip('.')
            output_format = output_format.lower()
            
            logger.info(f"Converting document: {input_ext} -> {output_format}")
            
            # Generate output path
            output_path = os.path.splitext(input_path)[0] + f'_converted.{output_format}'
            
            # Handle unsupported formats
            if output_format in ['torrent', 'zip', 'rar']:
                raise Exception(f"Cannot convert to {output_format.upper()} - unsupported format")
            
            # Route to specific conversion method
            if input_ext == 'pdf':
                return await self._convert_from_pdf(input_path, output_path, output_format)
            elif output_format == 'pdf':
                return await self._convert_to_pdf(input_path, output_path, input_ext)
            else:
                # Try specific converters first, then LibreOffice
                return await self._convert_with_fallback(input_path, output_path, input_ext, output_format)
                
        except Exception as e:
            logger.error(f"Document conversion error: {e}")
            raise Exception(f"Document conversion failed: {str(e)}")
    
    async def _convert_from_pdf(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert PDF to other formats"""
        try:
            if output_format in ['docx', 'doc']:
                return await self._convert_pdf_to_docx(input_path, output_path)
            elif output_format == 'txt':
                return await self._convert_pdf_to_txt(input_path, output_path)
            elif output_format == 'html':
                return await self._convert_pdf_to_html(input_path, output_path)
            elif output_format in ['jpg', 'jpeg', 'png', 'webp']:
                return await self.convert_pdf_to_image(input_path, output_format)
            else:
                return await self._convert_with_libreoffice(input_path, output_path, output_format)
        except Exception as e:
            logger.error(f"PDF conversion error: {e}")
            raise Exception(f"PDF to {output_format} conversion failed")
    
    async def _convert_to_pdf(self, input_path: str, output_path: str, input_format: str) -> str:
        """Convert various formats to PDF"""
        try:
            # Use docx2pdf for Word documents
            if input_format in ['docx', 'doc']:
                try:
                    from docx2pdf import convert
                    convert(input_path, output_path)
                    return output_path
                except ImportError:
                    pass
            
            # Use LibreOffice for other formats
            return await self._convert_with_libreoffice(input_path, output_path, 'pdf')
                
        except Exception as e:
            logger.error(f"To PDF conversion error: {e}")
            raise Exception(f"{input_format} to PDF conversion failed")
    
    async def _convert_with_fallback(self, input_path: str, output_path: str, input_ext: str, output_format: str) -> str:
        """Try multiple conversion methods"""
        try:
            # Try LibreOffice first
            return await self._convert_with_libreoffice(input_path, output_path, output_format)
        except Exception as e:
            logger.warning(f"LibreOffice conversion failed, trying alternatives: {e}")
            
            # Try specific format handlers
            if input_ext == 'xlsx' and output_format == 'csv':
                return await self._convert_xlsx_to_csv(input_path, output_path)
            elif input_ext == 'csv' and output_format == 'xlsx':
                return await self._convert_csv_to_xlsx(input_path, output_path)
            elif input_ext == 'txt' and output_format == 'html':
                return await self._convert_txt_to_html(input_path, output_path)
            else:
                raise Exception(f"No conversion method available for {input_ext} to {output_format}")
    
    async def _convert_pdf_to_docx(self, input_path: str, output_path: str) -> str:
        """Convert PDF to DOCX using pdf2docx"""
        try:
            from pdf2docx import Converter
            
            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            return output_path
            
        except ImportError:
            # Fallback to LibreOffice
            return await self._convert_with_libreoffice(input_path, output_path, 'docx')
    
    async def _convert_pdf_to_txt(self, input_path: str, output_path: str) -> str:
        """Convert PDF to text"""
        try:
            import pdfplumber
            
            text = ""
            with pdfplumber.open(input_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(text)
            
            return output_path
            
        except ImportError:
            # Try PyMuPDF as fallback
            try:
                import fitz
                doc = fitz.open(input_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                
                async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                    await f.write(text)
                return output_path
            except ImportError:
                return await self._convert_with_libreoffice(input_path, output_path, 'txt')
    
    async def _convert_pdf_to_html(self, input_path: str, output_path: str) -> str:
        """Convert PDF to HTML"""
        try:
            # Use PyMuPDF for PDF to HTML
            import fitz
            doc = fitz.open(input_path)
            html_content = ""
            for page in doc:
                html_content += page.get_text("html")
            
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)
            return output_path
        except ImportError:
            return await self._convert_with_libreoffice(input_path, output_path, 'html')
    
    async def convert_pdf_to_image(self, input_path: str, output_format: str) -> str:
        """Convert PDF to image"""
        try:
            from pdf2image import convert_from_path
            
            images = convert_from_path(input_path, dpi=150, first_page=1, last_page=1)
            if images:
                output_path = os.path.splitext(input_path)[0] + f'_page1.{output_format}'
                images[0].save(output_path, output_format.upper())
                return output_path
            else:
                raise Exception("No pages found in PDF")
                
        except ImportError:
            # Use PyMuPDF as fallback
            try:
                import fitz
                doc = fitz.open(input_path)
                page = doc[0]
                pix = page.get_pixmap()
                output_path = os.path.splitext(input_path)[0] + f'_page1.{output_format}'
                pix.save(output_path)
                return output_path
            except ImportError:
                raise Exception("PDF to image conversion requires pdf2image or PyMuPDF")
    
    async def _convert_xlsx_to_csv(self, input_path: str, output_path: str) -> str:
        """Convert Excel to CSV"""
        try:
            import pandas as pd
            
            # Read first sheet
            df = pd.read_excel(input_path)
            df.to_csv(output_path, index=False)
            return output_path
            
        except ImportError:
            return await self._convert_with_libreoffice(input_path, output_path, 'csv')
    
    async def _convert_csv_to_xlsx(self, input_path: str, output_path: str) -> str:
        """Convert CSV to Excel"""
        try:
            import pandas as pd
            
            df = pd.read_csv(input_path)
            df.to_excel(output_path, index=False)
            return output_path
            
        except ImportError:
            return await self._convert_with_libreoffice(input_path, output_path, 'xlsx')
    
    async def _convert_txt_to_html(self, input_path: str, output_path: str) -> str:
        """Convert text to HTML"""
        try:
            async with aiofiles.open(input_path, 'r', encoding='utf-8') as f:
                text = await f.read()
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Converted Document</title>
</head>
<body>
    <pre>{text}</pre>
</body>
</html>"""
            
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)
            return output_path
        except Exception as e:
            raise Exception(f"Text to HTML conversion failed: {str(e)}")
    
    async def _convert_with_libreoffice(self, input_path: str, output_path: str, output_format: str) -> str:
        """Universal conversion using LibreOffice with better error handling"""
        try:
            # Check if LibreOffice is available
            result = await self._run_command(['which', 'libreoffice'])
            if not result.strip():
                raise Exception("LibreOffice is not installed")
            
            cmd = [
                'libreoffice', '--headless', '--convert-to', output_format,
                '--outdir', os.path.dirname(output_path), input_path
            ]
            
            await self._run_command(cmd)
            
            # Find the converted file
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            expected_ext = '.' + output_format
            possible_path = os.path.join(os.path.dirname(output_path), base_name + expected_ext)
            
            if os.path.exists(possible_path):
                if possible_path != output_path:
                    os.rename(possible_path, output_path)
                return output_path
            else:
                # Try with different extensions
                for ext in [output_format, 'pdf', 'docx', 'txt']:
                    possible_path = os.path.join(os.path.dirname(output_path), base_name + '.' + ext)
                    if os.path.exists(possible_path):
                        if possible_path != output_path:
                            os.rename(possible_path, output_path)
                        return output_path
                
                raise Exception("LibreOffice conversion failed - output not found")
                
        except Exception as e:
            logger.error(f"LibreOffice conversion error: {e}")
            raise Exception(f"Conversion to {output_format} failed: {str(e)}")
    
    async def convert_images_to_pdf(self, image_paths: List[str], output_path: str) -> str:
        """Convert multiple images to PDF"""
        try:
            import img2pdf
            
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(image_paths))
            return output_path
                
        except ImportError:
            # Use PIL as fallback
            try:
                from PIL import Image
                
                images = []
                for img_path in image_paths:
                    img = Image.open(img_path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img)
                
                if images:
                    images[0].save(output_path, save_all=True, append_images=images[1:])
                    return output_path
                else:
                    raise Exception("No images to convert")
            except ImportError:
                raise Exception("Image to PDF conversion requires img2pdf or PIL")
    
    async def _run_command(self, cmd: List[str]) -> str:
        """Run system command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Command failed: {cmd} - {error_msg}")
                raise Exception(f"Command failed: {error_msg}")
            
            return stdout.decode() if stdout else ""
            
        except FileNotFoundError:
            raise Exception(f"Command not found: {cmd[0]}")
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise Exception(f"Conversion failed: {str(e)}")

# Global instance
doc_converter = DocumentConverter()