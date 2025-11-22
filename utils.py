import os
from PyPDF2 import PdfReader
import pdfplumber
from PIL import Image
import pytesseract
import io

def extract_text_from_pdf(file_path):
    """Extract text from PDF using multiple methods"""
    text = ""
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber error: {e}")
    
    if not text.strip():
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2 error: {e}")
    
    return text.strip()

def extract_text_from_images_in_pdf(file_path):
    """Extract text from images in PDF using OCR"""
    text = ""
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                images = page.images
                
                for img in images:
                    try:
                        bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                        page_image = page.within_bbox(bbox).to_image()
                        
                        pil_image = page_image.original
                        
                        ocr_text = pytesseract.image_to_string(pil_image)
                        if ocr_text.strip():
                            text += ocr_text + "\n"
                    except Exception as img_error:
                        print(f"Error processing image on page {page_num}: {img_error}")
                        continue
    except Exception as e:
        print(f"OCR extraction error: {e}")
    
    return text.strip()

def process_pdf_file(file_path):
    """Process PDF file with text extraction and OCR"""
    text = extract_text_from_pdf(file_path)
    
    if not text or len(text) < 100:
        ocr_text = extract_text_from_images_in_pdf(file_path)
        if ocr_text:
            text = text + "\n" + ocr_text if text else ocr_text
    
    return text

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_text(text):
    """Clean and normalize text"""
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line]
    
    return '\n'.join(lines)
