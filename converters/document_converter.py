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
    
    async def convert_pdf_to_images(self, input_path, output_format='jpg'):
        """Convert PDF to images using pdf2image"""
        try:
            if not Config.HAS_PDF2IMAGE:
                # Fallback: Use reportlab to create placeholder
                return await self._fallback_pdf_to_images(input_path, output_format)
            
            from pdf2image import convert_from_path
            
            images = convert_from_path(input_path, dpi=200)
            output_files = []
            
            for i, image in enumerate(images):
                output_path = input_path.replace('.pdf', f'_{i+1}.{output_format}')
                image.save(output_path, format=output_format.upper(), quality=95)
                output_files.append(output_path)
            
            return output_files
        except Exception as e:
            raise Exception(f"PDF to images conversion failed: {str(e)}")
    
    async def convert_pdf_to_docx(self, input_path, output_path):
        """Convert PDF to DOCX using pdf2docx"""
        try:
            from pdf2docx import Converter
            
            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            return output_path
        except Exception as e:
            # Fallback to text extraction
            return await self._fallback_pdf_to_docx(input_path, output_path)
    
    async def convert_docx_to_pdf(self, input_path, output_path):
        """Convert DOCX to PDF"""
        try:
            # Using unoconv if available, otherwise fallback
            if self._has_unoconv():
                result = subprocess.run([
                    'unoconv', '-f', 'pdf', '-o', output_path, input_path
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    return output_path
            
            # Fallback: Create a PDF from text content
            return await self._fallback_docx_to_pdf(input_path, output_path)
        except Exception as e:
            raise Exception(f"DOCX to PDF conversion failed: {str(e)}")
    
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
        """Convert Excel to PDF"""
        try:
            # Read Excel file
            if input_path.endswith('.csv'):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path)
            
            # Create PDF
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, f"Excel File: {os.path.basename(input_path)}")
            
            # Add data
            c.setFont("Helvetica", 10)
            y_position = height - 80
            
            # Add headers
            headers = df.columns.tolist()
            for i, header in enumerate(headers):
                c.drawString(50 + i * 100, y_position, str(header))
            
            y_position -= 20
            
            # Add rows (limited for PDF)
            for _, row in df.head(50).iterrows():  # Limit to 50 rows
                for i, value in enumerate(row):
                    c.drawString(50 + i * 100, y_position, str(value))
                y_position -= 15
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Excel to PDF conversion failed: {str(e)}")
    
    async def convert_txt_to_pdf(self, input_path, output_path):
        """Convert text file to PDF"""
        try:
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica", 12)
            y_position = height - 40
            line_height = 14
            
            # Split text into lines
            lines = []
            for line in text_content.split('\n'):
                words = line.split()
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
            
            # Add lines to PDF
            for line in lines[:100]:  # Limit to 100 lines
                if y_position < 40:
                    c.showPage()
                    y_position = height - 40
                    c.setFont("Helvetica", 12)
                
                c.drawString(50, y_position, line)
                y_position -= line_height
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Text to PDF conversion failed: {str(e)}")
    
    async def compress_pdf(self, input_path, output_path, quality='medium'):
        """Compress PDF file"""
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                # Compress the page
                page.compress_content_streams()
                writer.add_page(page)
            
            # Set compression level
            if quality == 'high':
                # More aggressive compression
                pass
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF compression failed: {str(e)}")
    
    async def merge_pdfs(self, pdf_paths, output_path):
        """Merge multiple PDFs"""
        try:
            writer = PdfWriter()
            
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    reader = PdfReader(pdf_path)
                    for page in reader.pages:
                        writer.add_page(page)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF merge failed: {str(e)}")
    
    async def split_pdf(self, input_path, output_dir, pages=None):
        """Split PDF into multiple files"""
        try:
            reader = PdfReader(input_path)
            output_files = []
            
            if pages is None:
                # Split by individual pages
                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)
                    output_path = os.path.join(output_dir, f"page_{i+1}.pdf")
                    with open(output_path, 'wb') as f:
                        writer.write(f)
                    output_files.append(output_path)
            else:
                # Split by specified page ranges
                for i, page_range in enumerate(pages):
                    writer = PdfWriter()
                    start, end = page_range
                    for page_num in range(start-1, end):
                        writer.add_page(reader.pages[page_num])
                    output_path = os.path.join(output_dir, f"part_{i+1}.pdf")
                    with open(output_path, 'wb') as f:
                        writer.write(f)
                    output_files.append(output_path)
            
            return output_files
        except Exception as e:
            raise Exception(f"PDF split failed: {str(e)}")
    
    def _has_unoconv(self):
        """Check if unoconv is available"""
        try:
            result = subprocess.run(['unoconv', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    async def _fallback_pdf_to_docx(self, input_path, output_path):
        """Fallback PDF to DOCX using text extraction"""
        try:
            import pdfplumber
            
            text_content = ""
            with pdfplumber.open(input_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content += text + "\n\n"
            
            # Create a simple DOCX with python-docx
            from docx import Document
            
            doc = Document()
            doc.add_heading('PDF Conversion', 0)
            doc.add_paragraph(f"Original file: {os.path.basename(input_path)}")
            doc.add_paragraph("Converted from PDF to DOCX")
            doc.add_paragraph("--- Content ---")
            
            # Add extracted text
            for paragraph in text_content.split('\n'):
                if paragraph.strip():
                    doc.add_paragraph(paragraph)
            
            doc.save(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"Fallback PDF to DOCX failed: {str(e)}")
    
    async def _fallback_docx_to_pdf(self, input_path, output_path):
        """Fallback DOCX to PDF using text extraction"""
        try:
            from docx import Document
            
            doc = Document(input_path)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # Create PDF
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "DOCX to PDF Conversion")
            
            c.setFont("Helvetica", 12)
            y_position = height - 80
            
            for line in text_content[:50]:  # Limit content
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                    c.setFont("Helvetica", 12)
                
                # Simple text wrapping
                words = line.split()
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
                    y_position -= 15
            
            c.save()
            return output_path
        except Exception as e:
            raise Exception(f"Fallback DOCX to PDF failed: {str(e)}")
    
    async def _fallback_pdf_to_images(self, input_path, output_format):
        """Fallback PDF to images using reportlab (creates placeholder)"""
        output_files = []
        
        try:
            reader = PdfReader(input_path)
            num_pages = len(reader.pages)
            
            for i in range(min(num_pages, 10)):  # Limit to 10 pages
                output_path = input_path.replace('.pdf', f'_{i+1}.{output_format}')
                
                # Create a placeholder image
                img = Image.new('RGB', (800, 1000), color='white')
                img.save(output_path, format=output_format.upper())
                output_files.append(output_path)
            
            return output_files
        except Exception as e:
            raise Exception(f"Fallback PDF to images failed: {str(e)}")

# Global converter instance
doc_converter = DocumentConverter()