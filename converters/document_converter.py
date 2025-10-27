import os
import asyncio
from PIL import Image
import img2pdf
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import pandas as pd
from config import Config
import subprocess
import sys
import fitz  # PyMuPDF for better PDF handling
import logging

logger = logging.getLogger(__name__)

class DocumentConverter:
    def __init__(self):
        self.supported_conversions = {
            'pdf_to_docx': (['pdf'], 'docx'),
            'pdf_to_images': (['pdf'], 'images'),
            'docx_to_pdf': (['docx', 'doc'], 'pdf'),
            'images_to_pdf': (['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff'], 'pdf'),
            'excel_to_pdf': (['xlsx', 'xls', 'csv'], 'pdf'),
            'ppt_to_pdf': (['pptx', 'ppt'], 'pdf'),
            'html_to_pdf': (['html', 'htm'], 'pdf'),
            'txt_to_pdf': (['txt'], 'pdf'),
            'markdown_to_pdf': (['md', 'markdown'], 'pdf')
        }
    
    async def convert_document(self, input_path, output_format):
        """Main document conversion method that routes to specific converters"""
        try:
            input_extension = input_path.split('.')[-1].lower()
            
            if input_extension == 'pdf':
                if output_format == 'txt':
                    output_path = input_path.rsplit('.', 1)[0] + '.txt'
                    return await self.convert_pdf_to_txt(input_path, output_path)
                elif output_format == 'docx':
                    output_path = input_path.rsplit('.', 1)[0] + '.docx'
                    return await self.convert_pdf_to_docx(input_path, output_path)
                elif output_format in ['jpg', 'png', 'jpeg']:
                    images = await self.convert_pdf_to_images(input_path, output_format)
                    return images[0] if images else None
                else:
                    raise Exception(f"PDF to {output_format} conversion not supported")
            
            elif input_extension in ['docx', 'doc']:
                if output_format == 'pdf':
                    output_path = input_path.rsplit('.', 1)[0] + '.pdf'
                    return await self.convert_docx_to_pdf(input_path, output_path)
                elif output_format == 'txt':
                    output_path = input_path.rsplit('.', 1)[0] + '.txt'
                    return await self.convert_docx_to_txt(input_path, output_path)
                else:
                    raise Exception(f"DOCX to {output_format} conversion not supported")
            
            elif input_extension == 'txt':
                if output_format == 'pdf':
                    output_path = input_path.rsplit('.', 1)[0] + '.pdf'
                    return await self.convert_txt_to_pdf(input_path, output_path)
                else:
                    raise Exception(f"TXT to {output_format} conversion not supported")
            
            elif input_extension in ['xlsx', 'xls', 'csv']:
                if output_format == 'pdf':
                    output_path = input_path.rsplit('.', 1)[0] + '.pdf'
                    return await self.convert_excel_to_pdf(input_path, output_path)
                else:
                    raise Exception(f"Excel to {output_format} conversion not supported")
            
            elif input_extension in ['pptx', 'ppt']:
                if output_format == 'pdf':
                    output_path = input_path.rsplit('.', 1)[0] + '.pdf'
                    return await self.convert_ppt_to_pdf(input_path, output_path)
                else:
                    raise Exception(f"PowerPoint to {output_format} conversion not supported")
            
            elif input_extension in ['html', 'htm']:
                if output_format == 'pdf':
                    output_path = input_path.rsplit('.', 1)[0] + '.pdf'
                    return await self.convert_html_to_pdf(input_path, output_path)
                else:
                    raise Exception(f"HTML to {output_format} conversion not supported")
            
            else:
                raise Exception(f"Document conversion from {input_extension} to {output_format} not supported")
                
        except Exception as e:
            logger.error(f"Document conversion error: {e}")
            raise
    
    async def convert_pdf_to_txt(self, input_path, output_path):
        """Convert PDF to TXT using PyMuPDF for accurate text extraction"""
        try:
            doc = fitz.open(input_path)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_content += f"--- Page {page_num + 1} ---\n{text}\n\n"
            
            doc.close()
            
            # Save as UTF-8 text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to TXT conversion failed: {str(e)}")
    
    async def convert_docx_to_txt(self, input_path, output_path):
        """Convert DOCX to TXT"""
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
            raise Exception(f"DOCX to TXT conversion failed: {str(e)}")
    
    async def convert_pdf_to_images(self, input_path, output_format='jpg'):
        """Convert PDF to images using pdf2image"""
        try:
            from pdf2image import convert_from_path
            
            images = convert_from_path(input_path, dpi=200)
            output_files = []
            
            for i, image in enumerate(images):
                output_path = input_path.replace('.pdf', f'_{i+1}.{output_format}')
                image.save(output_path, format=output_format.upper(), quality=95)
                output_files.append(output_path)
            
            return output_files
        except Exception as e:
            # Fallback using PyMuPDF
            return await self._fallback_pdf_to_images(input_path, output_format)
    
    async def convert_pdf_to_docx(self, input_path, output_path):
        """Convert PDF to DOCX using pdf2docx"""
        try:
            from pdf2docx import Converter
            
            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            return output_path
        except Exception as e:
            # Fallback to text extraction with better formatting
            return await self._fallback_pdf_to_docx(input_path, output_path)
    
    async def convert_docx_to_pdf(self, input_path, output_path):
        """Convert DOCX to PDF using docx2pdf"""
        try:
            from docx2pdf import convert
            
            convert(input_path, output_path)
            return output_path
        except Exception as e:
            # Fallback using python-docx and reportlab
            return await self._fallback_docx_to_pdf(input_path, output_path)
    
    async def convert_images_to_pdf(self, image_paths, output_path):
        """Convert multiple images to PDF"""
        try:
            # Validate and convert all images
            valid_images = []
            for img_path in image_paths:
                if os.path.exists(img_path):
                    # Open and validate image
                    with Image.open(img_path) as img:
                        img = img.convert('RGB')
                        valid_images.append(img_path)
            
            if not valid_images:
                raise Exception("No valid images found")
            
            # Convert images to PDF
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(valid_images))
            
            return output_path
        except Exception as e:
            raise Exception(f"Images to PDF conversion failed: {str(e)}")
    
    async def convert_excel_to_pdf(self, input_path, output_path):
        """Convert Excel to PDF with proper formatting"""
        try:
            # Read Excel file
            if input_path.endswith('.csv'):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path)
            
            # Create PDF with better formatting
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, f"Excel File: {os.path.basename(input_path)}")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, f"Total Rows: {len(df)}, Columns: {len(df.columns)}")
            
            # Add data with table formatting
            y_position = height - 100
            row_height = 15
            col_width = 80
            
            # Add headers with background
            headers = df.columns.tolist()
            c.setFillColorRGB(0.8, 0.8, 0.8)  # Gray background
            c.rect(50, y_position - 5, len(headers) * col_width, row_height + 5, fill=1)
            c.setFillColorRGB(0, 0, 0)  # Black text
            
            c.setFont("Helvetica-Bold", 10)
            for i, header in enumerate(headers):
                c.drawString(55 + i * col_width, y_position, str(header)[:15])  # Truncate long headers
            
            y_position -= row_height + 5
            c.setFont("Helvetica", 9)
            
            # Add rows (limited for PDF)
            for row_idx, (_, row) in enumerate(df.head(30).iterrows()):  # Limit to 30 rows
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                    c.setFont("Helvetica", 9)
                
                for i, value in enumerate(row):
                    text = str(value)[:20]  # Truncate long values
                    c.drawString(55 + i * col_width, y_position, text)
                
                y_position -= row_height
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Excel to PDF conversion failed: {str(e)}")
    
    async def convert_ppt_to_pdf(self, input_path, output_path):
        """Convert PowerPoint to PDF"""
        try:
            from pptx import Presentation
            
            # This is a basic implementation - in production you'd use better tools
            prs = Presentation(input_path)
            
            # Create a simple PDF representation
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
                        # Simple text wrapping
                        words = shape.text.split()
                        current_line = []
                        
                        for word in words:
                            test_line = ' '.join(current_line + [word])
                            if c.stringWidth(test_line, "Helvetica", 12) < (width - 100):
                                current_line.append(word)
                            else:
                                if current_line:
                                    c.drawString(50, y_position, ' '.join(current_line))
                                    y_position -= 15
                                current_line = [word]
                        
                        if current_line:
                            c.drawString(50, y_position, ' '.join(current_line))
                            y_position -= 20
                
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"PowerPoint to PDF conversion failed: {str(e)}")
    
    async def convert_html_to_pdf(self, input_path, output_path):
        """Convert HTML to PDF"""
        try:
            # Simple HTML to PDF conversion using reportlab
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "HTML to PDF Conversion")
            
            c.setFont("Helvetica", 12)
            y_position = height - 80
            
            # Extract text content (basic implementation)
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)  # Remove HTML tags
            lines = text_content.split('\n')
            
            for line in lines[:50]:  # Limit content
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                    c.setFont("Helvetica", 12)
                
                if line.strip():
                    c.drawString(50, y_position, line[:80])  # Truncate long lines
                    y_position -= 15
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"HTML to PDF conversion failed: {str(e)}")
    
    async def convert_txt_to_pdf(self, input_path, output_path):
        """Convert text file to PDF with proper formatting"""
        try:
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 40, f"Text File: {os.path.basename(input_path)}")
            
            c.setFont("Helvetica", 12)
            y_position = height - 70
            line_height = 14
            margin = 50
            max_width = width - 2 * margin
            
            # Split text into lines with proper wrapping
            lines = []
            for paragraph in text_content.split('\n'):
                words = paragraph.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    text_width = c.stringWidth(test_line, "Helvetica", 12)
                    
                    if text_width < max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(' '.join(current_line))
                lines.append('')  # Empty line between paragraphs
            
            # Add lines to PDF
            for line in lines[:200]:  # Limit to 200 lines
                if y_position < 40:
                    c.showPage()
                    y_position = height - 40
                    c.setFont("Helvetica", 12)
                
                if line.strip():  # Only draw non-empty lines
                    c.drawString(margin, y_position, line)
                y_position -= line_height
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Text to PDF conversion failed: {str(e)}")
    
    async def compress_pdf(self, input_path, output_path, quality='medium'):
        """Compress PDF file with different quality levels"""
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                # Compress the page
                page.compress_content_streams()
                writer.add_page(page)
            
            # Set compression level
            compression_level = {
                'low': 0,
                'medium': 5,
                'high': 9
            }.get(quality, 5)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF compression failed: {str(e)}")
    
    async def _fallback_pdf_to_docx(self, input_path, output_path):
        """Fallback PDF to DOCX using text extraction with PyMuPDF"""
        try:
            doc = fitz.open(input_path)
            
            from docx import Document
            from docx.shared import Inches
            
            document = Document()
            document.add_heading('PDF Conversion', 0)
            document.add_paragraph(f"Original file: {os.path.basename(input_path)}")
            document.add_paragraph(f"Total pages: {len(doc)}")
            document.add_paragraph("--- Content ---")
            
            # Add extracted text with page markers
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    document.add_heading(f'Page {page_num + 1}', level=2)
                    for paragraph in text.split('\n'):
                        if paragraph.strip():
                            document.add_paragraph(paragraph)
            
            doc.close()
            document.save(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"Fallback PDF to DOCX failed: {str(e)}")
    
    async def _fallback_docx_to_pdf(self, input_path, output_path):
        """Fallback DOCX to PDF using python-docx and reportlab"""
        try:
            from docx import Document
            
            doc = Document(input_path)
            text_content = []
            
            # Extract all text content
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # Create PDF with better formatting
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "DOCX to PDF Conversion")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, f"Original: {os.path.basename(input_path)}")
            
            c.setFont("Helvetica", 12)
            y_position = height - 100
            line_height = 14
            margin = 50
            max_width = width - 2 * margin
            
            # Add content with proper wrapping
            for paragraph in text_content[:100]:  # Limit content
                words = paragraph.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    text_width = c.stringWidth(test_line, "Helvetica", 12)
                    
                    if text_width < max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            if y_position < 50:
                                c.showPage()
                                y_position = height - 50
                                c.setFont("Helvetica", 12)
                            c.drawString(margin, y_position, ' '.join(current_line))
                            y_position -= line_height
                        current_line = [word]
                
                if current_line:
                    if y_position < 50:
                        c.showPage()
                        y_position = height - 50
                        c.setFont("Helvetica", 12)
                    c.drawString(margin, y_position, ' '.join(current_line))
                    y_position -= line_height
                
                # Add space between paragraphs
                y_position -= line_height / 2
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Fallback DOCX to PDF failed: {str(e)}")
    
    async def _fallback_pdf_to_images(self, input_path, output_format):
        """Fallback PDF to images using PyMuPDF"""
        try:
            doc = fitz.open(input_path)
            output_files = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
                
                output_path = input_path.replace('.pdf', f'_{page_num+1}.{output_format}')
                pix.save(output_path)
                output_files.append(output_path)
            
            doc.close()
            return output_files
        except Exception as e:
            raise Exception(f"Fallback PDF to images failed: {str(e)}")

# Global converter instance
doc_converter = DocumentConverter()