"""
Multi-modal file processor for AI Intelligence Hub.
Handles: PDF (text + OCR), Images (captioning), Text files, Office docs.
Audio transcription has been removed as it is not required for this build.
"""

import os
import io
import tempfile
import traceback
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_IMAGE = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

# Supported file extensions (Audio removed)
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'webp', 'tiff', 'tif'}
TEXT_EXTENSIONS = {'txt', 'md', 'csv', 'json', 'xml', 'html', 'log', 'py'}
OFFICE_EXTENSIONS = {'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'}

class FileProcessingError(Exception):
    """Custom exception for file processing failures."""
    pass


async def process_uploaded_file(file) -> str:
    """
    Main entry point - processes any uploaded file and returns text representation.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        str: Extracted text content or error message
    """
    try:
        content = await file.read()
        
        if not content:
            return f"[File '{file.filename}' is empty.]"

        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower().lstrip('.')
        
        print(f"📂 Processing file: {filename} (Type: .{ext})")
        
        # Route to appropriate handler
        if ext == 'pdf':
            return _process_pdf(content, filename)
        
        if ext in IMAGE_EXTENSIONS:
            return _process_image(content, filename)
        
        if ext in TEXT_EXTENSIONS:
            return _process_text(content, filename)
        
        # Office & Document formats
        if ext in OFFICE_EXTENSIONS:
            if ext in ['docx', 'doc']:
                return _process_docx(content, filename)
            if ext in ['pptx', 'ppt']:
                return _process_pptx(content, filename)
            if ext in ['xlsx', 'xls']:
                return _process_excel(content, filename)
        
        return f"[Unsupported file type: .{ext}]"

    except Exception as e:
        print(f"❌ Error processing '{file.filename}': {e}")
        traceback.print_exc()
        return f"[Could not process '{file.filename}'. Please try again or use a different file format.]"


# ===================================================================
# PDF PROCESSING
# ===================================================================

def _process_pdf(content: bytes, filename: str) -> str:
    """
    Process PDF with automatic fallback chain:
    1. Try text extraction (pdfplumber)
    2. Try PyPDF2
    3. Try pdfminer
    4. Try OCR on each page (pytesseract + pdf2image)
    5. Return clear error if all fail
    """
    tmp_path = _save_temp_file(content, suffix='.pdf')
    
    try:
        # Step 1: Try direct text extraction
        extracted_text = _extract_text_from_pdf(tmp_path)
        
        if extracted_text and len(extracted_text.strip()) > 50:
            return f"[PDF Content - {filename}]\n\n{extracted_text}"
        
        # Step 2: Text extraction failed - try OCR
        print(f"🔍 No text found in PDF, attempting OCR...")
        ocr_text = _ocr_pdf(tmp_path, filename)
        
        if ocr_text and len(ocr_text.strip()) > 50:
            return f"[PDF Content (OCR) - {filename}]\n\n{ocr_text}"
        
        # Step 3: Both failed
        return _format_pdf_error(filename)
    
    finally:
        _cleanup_temp_file(tmp_path)


def _extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text using multiple PDF libraries.
    Returns text if successful, None if all methods fail.
    """
    methods = [
        _try_pdfplumber,
        _try_pypdf2,
        _try_pdfminer,
    ]
    
    for method in methods:
        try:
            text = method(pdf_path)
            if text and text.strip():
                return text.strip()
        except Exception:
            continue
    
    return None


def _try_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (best for formatted PDFs)."""
    import pdfplumber
    
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = []
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(f"--- Page {i} ---\n{text}")
        return "\n\n".join(pages_text)


def _try_pypdf2(pdf_path: str) -> str:
    """Extract text using PyPDF2 (good fallback)."""
    from PyPDF2 import PdfReader
    
    reader = PdfReader(pdf_path)
    pages_text = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text and text.strip():
            pages_text.append(f"--- Page {i} ---\n{text}")
    return "\n\n".join(pages_text)


def _try_pdfminer(pdf_path: str) -> str:
    """Extract text using pdfminer.six (low-level, catches missed text)."""
    from pdfminer.high_level import extract_text
    return extract_text(pdf_path)


def _ocr_pdf(pdf_path: str, filename: str) -> Optional[str]:
    """
    Perform OCR on PDF pages.
    Converts each page to image, then runs Tesseract OCR.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=300)
        
        ocr_pages = []
        for i, image in enumerate(images, 1):
            print(f"  📷 OCR processing page {i}/{len(images)}...")
            text = pytesseract.image_to_string(image, lang='eng')
            if text and text.strip():
                ocr_pages.append(f"--- Page {i} ---\n{text}")
        
        return "\n\n".join(ocr_pages) if ocr_pages else None
    
    except ImportError as e:
        print(f"⚠️ OCR libraries not installed: {e}")
        return None
    except Exception as e:
        print(f"⚠️ OCR failed: {e}")
        return None


def _format_pdf_error(filename: str) -> str:
    """Create helpful error message for unreadable PDFs."""
    return (
        f"[Could not read '{filename}'. This PDF may be:\n"
        f"• A scanned document (images only, no text)\n"
        f"• Password protected\n"
        f"• Corrupted or malformed\n\n"
        f"Solutions:\n"
        f"1. If scanned: Install OCR support (pip install pytesseract pdf2image)\n"
        f"2. If protected: Remove password before uploading\n"
        f"3. Copy-paste the text directly into chat"
    )


# ===================================================================
# IMAGE PROCESSING
# ===================================================================

def _process_image(content: bytes, filename: str) -> str:
    """Generate caption for image using Hugging Face BLIP model."""
    tmp_path = _save_temp_file(content, suffix='.jpg')
    
    try:
        if not HF_TOKEN:
            return f"[Image: {filename}] - No HF_TOKEN set. Cannot analyze image."
            
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        with open(tmp_path, "rb") as f:
            resp = requests.post(HF_API_IMAGE, headers=headers, data=f.read(), timeout=30)
        
        if resp.status_code != 200:
            return f"[Image analysis failed: HTTP {resp.status_code}]"
        
        result = resp.json()
        
        if isinstance(result, list) and len(result) > 0:
            caption = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            caption = result.get("generated_text", str(result))
        else:
            caption = str(result)
        
        return f"[Image: {filename}]\nDescription: {caption}" if caption else f"[Image: {filename} - No description generated]"
    
    except Exception as e:
        print(f"❌ Image processing error: {e}")
        return f"[Could not analyze image '{filename}'. Error: {str(e)}]"
    finally:
        _cleanup_temp_file(tmp_path)


# ===================================================================
# OFFICE & DOCUMENT PROCESSING
# ===================================================================

def _process_docx(content: bytes, filename: str) -> str:
    """Extract text from Word (.docx) files."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        texts = []
        for para in doc.paragraphs:
            if para.text.strip():
                texts.append(para.text)
        return f"[Word Document: {filename}]\n\n" + "\n".join(texts)
    except ImportError:
        return f"[Word document support requires: pip install python-docx]"
    except Exception as e:
        return f"[Error extracting DOCX: {str(e)}]"


def _process_pptx(content: bytes, filename: str) -> str:
    """Extract text from PowerPoint (.pptx) files."""
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(content))
        texts = []
        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)
            if slide_text:
                texts.append(f"[Slide {slide_num}]\n" + "\n".join(slide_text))
        return f"[PowerPoint: {filename}]\n\n" + "\n\n".join(texts)
    except ImportError:
        return f"[PowerPoint support requires: pip install python-pptx]"
    except Exception as e:
        return f"[Error extracting PPTX: {str(e)}]"


def _process_excel(content: bytes, filename: str) -> str:
    """Extract text from Excel (.xlsx/.xls) files."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(content), data_only=True)
        texts = []
        for sheet in wb.worksheets:
            sheet_text = []
            for row in sheet.iter_rows(values_only=True):
                row_text = " | ".join([str(cell) for cell in row if cell is not None])
                if row_text.strip():
                    sheet_text.append(row_text)
            if sheet_text:
                texts.append(f"[Sheet: {sheet.title}]\n" + "\n".join(sheet_text))
        return f"[Excel: {filename}]\n\n" + "\n\n".join(texts)
    except ImportError:
        return f"[Excel support requires: pip install openpyxl]"
    except Exception as e:
        return f"[Error extracting Excel: {str(e)}]"


# ===================================================================
# TEXT PROCESSING
# ===================================================================

def _process_text(content: bytes, filename: str) -> str:
    """Read plain text files with encoding detection."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            text = content.decode(encoding)
            return f"[File: {filename}]\n\n{text}"
        except UnicodeDecodeError:
            continue
    
    return f"[Could not decode text file '{filename}'. Unsupported encoding.]"


# ===================================================================
# UTILITY FUNCTIONS
# ===================================================================

def _save_temp_file(content: bytes, suffix: str = '') -> str:
    """Save bytes to a temporary file and return path."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        return tmp.name


def _cleanup_temp_file(path: str) -> None:
    """Safely remove temporary file."""
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        print(f"⚠️ Could not delete temp file {path}: {e}")