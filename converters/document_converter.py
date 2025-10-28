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
        self.supported_formats = ['pdf', 'docx', 'doc', 'txt', 'html', 'xlsx', 'xls', 'pptx', 'ppt', 'csv', 'odt', 'ods', 'odp', 'epub', 'mobi']
    
    async def convert_document(self, input_path: str, output_format: str) -> str:
        """Convert document to target format"""
        try:
            input_ext = os.path.splitext(input_path)[1].lower().lstrip('.')
            output_format = output_format.lower()
            
            logger.info(f"Converting document: {input_ext} -> {output_format}")
            
            # Generate output path
            output_path = os.path.splitext(input_path)[0] + f'_converted.{output_format}'
            
            # Route to specific conversion method
            if input_ext == 'pdf':
                return await self._convert_from_pdf(input_path, output_path, output_format)
            elif output_format == 'pdf':
                return await self._convert_to_pdf(input_path, output_path, input_ext)
            elif input_ext == 'docx' and output_format in ['doc', 'txt', 'html', 'odt']:
                return await self._convert_docx_to_other(input_path, output_path, output_format)
            elif input_ext == 'doc' and output_format in ['docx', 'txt', 'html', 'pdf']:
                return await self._convert_doc_to_other(input_path, output_path, output_format)
            elif input_ext == 'xlsx' and output_format == 'csv':
                return await self._convert_xlsx_to_csv(input_path, output_path)
            elif input_ext == 'csv' and output_format == 'xlsx':
                return await self._convert_csv_to_xlsx(input_path, output_path)
            elif input_ext == 'pptx' and output_format in ['pdf', 'html']:
                return await self._convert_pptx_to_other(input_path, output_path, output_format)
            elif input_ext == 'html' and output_format in ['pdf', 'txt', 'docx']:
                return await self._convert_html_to_other(input_path, output_path, output_format)
            elif input_ext == 'txt' and output_format in ['pdf', 'docx', 'html']:
                return await self._convert_txt_to_other(input_path, output_path, output_format)
            else:
                # Try LibreOffice as fallback
                return await self._convert_with_libreoffice(input_path, output_path, output_format)
                
        except Exception as e:
            logger.error(f"Document conversion error: {e}")
            raise Exception(f"PDF to {output_format} conversion not supported")
    
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
            elif output_format in ['pptx', 'ppt']:
                return await self._convert_pdf_to_pptx(input_path, output_path)
            elif output_format in ['xlsx', 'xls']:
                return await self._convert_pdf_to_xlsx(input_path, output_path)
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
            cmd = [
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path), input_path
            ]
            
            await self._run_command(cmd)
            
            # LibreOffice creates file with .pdf extension
            expected_path = os.path.splitext(input_path)[0] + '.pdf'
            if os.path.exists(expected_path):
                if expected_path != output_path:
                    os.rename(expected_path, output_path)
                return output_path
            else:
                raise Exception("PDF conversion failed - output not found")
                
        except Exception as e:
            logger.error(f"To PDF conversion error: {e}")
            raise Exception(f"{input_format} to PDF conversion failed")
    
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
                raise Exception("PDF to text conversion requires pdfplumber or PyMuPDF")
    
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
            raise Exception("PDF to HTML conversion requires PyMuPDF")
    
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
    
    async def _convert_pdf_to_pptx(self, input_path: str, output_path: str) -> str:
        """Convert PDF to PowerPoint"""
        try:
            # Convert PDF to images first, then create PPTX
            from pdf2image import convert_from_path
            from pptx import Presentation
            from pptx.util import Inches
            
            images = convert_from_path(input_path, dpi=150)
            prs = Presentation()
            
            for image in images:
                # Create blank slide
                slide_layout = prs.slide_layouts[6]  # blank layout
                slide = prs.slides.add_slide(slide_layout)
                
                # Save temp image
                temp_img_path = os.path.join(tempfile.gettempdir(), f'temp_{id(image)}.png')
                image.save(temp_img_path, 'PNG')
                
                # Add image to slide
                left = top = Inches(0.5)
                slide.shapes.add_picture(temp_img_path, left, top, height=Inches(7))
                
                # Cleanup temp file
                os.remove(temp_img_path)
            
            prs.save(output_path)
            return output_path
            
        except ImportError:
            raise Exception("PDF to PPTX requires pdf2image and python-pptx")
    
    async def _convert_pdf_to_xlsx(self, input_path: str, output_path: str) -> str:
        """Convert PDF to Excel"""
        try:
            import tabula
            import pandas as pd
            
            # Extract tables from PDF
            tables = tabula.read_pdf(input_path, pages='all', multiple_tables=True)
            
            if not tables:
                raise Exception("No tables found in PDF")
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(output_path) as writer:
                for i, table in enumerate(tables):
                    sheet_name = f'Table_{i+1}'
                    table.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return output_path
            
        except ImportError:
            raise Exception("PDF to Excel requires tabula-py and pandas")
    
    async def _convert_docx_to_other(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert DOCX to other formats"""
        return await self._convert_with_libreoffice(input_path, output_path, output_format)
    
    async def _convert_doc_to_other(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert DOC to other formats"""
        return await self._convert_with_libreoffice(input_path, output_path, output_format)
    
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
    
    async def _convert_pptx_to_other(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert PowerPoint to other formats"""
        return await self._convert_with_libreoffice(input_path, output_path, output_format)
    
    async def _convert_html_to_other(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert HTML to other formats"""
        if output_format == 'pdf':
            try:
                import pdfkit
                pdfkit.from_file(input_path, output_path)
                return output_path
            except ImportError:
                return await self._convert_with_libreoffice(input_path, output_path, 'pdf')
        else:
            return await self._convert_with_libreoffice(input_path, output_path, output_format)
    
    async def _convert_txt_to_other(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert text to other formats"""
        if output_format == 'pdf':
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                
                c = canvas.Canvas(output_path, pagesize=letter)
                c.setFont("Helvetica", 12)
                
                async with aiofiles.open(input_path, 'r', encoding='utf-8') as f:
                    text = await f.read()
                
                y = 750
                for line in text.split('\n'):
                    if y < 50:
                        c.showPage()
                        c.setFont("Helvetica", 12)
                        y = 750
                    c.drawString(50, y, line[:80])  # Limit line length
                    y -= 15
                
                c.save()
                return output_path
                
            except ImportError:
                return await self._convert_with_libreoffice(input_path, output_path, 'pdf')
        else:
            return await self._convert_with_libreoffice(input_path, output_path, output_format)
    
    async def _convert_with_libreoffice(self, input_path: str, output_path: str, output_format: str) -> str:
        """Universal conversion using LibreOffice"""
        try:
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
                raise Exception("LibreOffice conversion failed - output not found")
                
        except Exception as e:
            logger.error(f"LibreOffice conversion error: {e}")
            raise Exception(f"Conversion to {output_format} failed")
    
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
                raise Exception(f"Command failed: {error_msg}")
            
            return stdout.decode() if stdout else ""
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise Exception(f"Conversion failed: {str(e)}")

# Global instance
doc_converter = DocumentConverter()