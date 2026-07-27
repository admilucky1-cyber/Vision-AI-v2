"""
Vision AI v2.0 - Multi-Modal File Processor (multimodal.py)
============================================================
Unified entry point for processing all supported file types.
Handles: PDF (text + OCR), Images (captioning), Text files, Office docs.

Supported formats:
- PDF: pdfplumber -> PyPDF2 -> pdfminer -> OCR (pytesseract)
- Images: JPG, PNG, BMP, WEBP, TIFF (BLIP captioning)
- Office: DOCX, PPTX, XLSX
- Text: TXT, MD, CSV, JSON, XML, HTML, LOG, PY
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

# ==========================================================
# CONFIGURATION
# ==========================================================
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_IMAGE = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

# Supported file extensions
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'webp', 'tiff', 'tif'}
TEXT_EXTENSIONS = {'txt', 'md', 'csv', 'json', 'xml', 'html', 'log', 'py'}
OFFICE_EXTENSIONS = {'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'}

# ==========================================================
# EXCEPTIONS
# ==========================================================
class FileProcessingError(Exception):
    """Custom exception for file processing failures."""
    pass

# ==========================================================
# MAIN PROCESSOR
# ==========================================================
async def process_uploaded_file(file) -> str:
    """
    Process any uploaded file and return text representation.

    Args:
        file: FastAPI UploadFile object

    Returns:
        Extracted text content or error message
    """
    try:
        content = await file.read()

        if not content:
            return f"[File '{file.filename}' is empty.]"

        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower().lstrip('.')

        # Route to appropriate handler
        if ext == 'pdf':
            return _process_pdf(content, filename)
        elif ext in IMAGE_EXTENSIONS:
            return _process_image(content, filename)
        elif ext in TEXT_EXTENSIONS:
            return _process_text(content, filename)
        elif ext in ['docx', 'doc']:
            return _process_docx(content, filename)
        elif ext in ['pptx', 'ppt']:
            return _process_pptx(content, filename)
        elif ext in ['xlsx', 'xls']:
            return _process_excel(content, filename)
        else:
            return f"[Unsupported file type: .{ext}]"

    except Exception as e:
        traceback.print_exc()
        return f"[Could not process '{file.filename}': {str(e)}]"

# ==========================================================
# PDF PROCESSING
# ==========================================================
def _process_pdf(content: bytes, filename: str) -> str:
    """Process PDF with automatic fallback chain."""
    tmp_path = _save_temp_file(content, suffix='.pdf')

    try:
        # Step 1: Try direct text extraction
        extracted_text = _extract_text_from_pdf(tmp_path)
        if extracted_text and len(extracted_text.strip()) > 50:
            return f"[PDF Content - {filename}]\n\n{extracted_text}"

        # Step 2: Try OCR (optional)
        ocr_text = _ocr_pdf(tmp_path, filename)
        if ocr_text and len(ocr_text.strip()) > 50:
            return f"[PDF Content (OCR) - {filename}]\n\n{ocr_text}"

        return _format_pdf_error(filename)
    finally:
        _cleanup_temp_file(tmp_path)

def _extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract text using multiple PDF libraries."""
    methods = [_try_pdfplumber, _try_pypdf2, _try_pdfminer]

    for method in methods:
        try:
            text = method(pdf_path)
            if text and text.strip():
                return text.strip()
        except Exception:
            continue
    return None

def _try_pdfplumber(pdf_path: str) -> str:
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = []
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(f"--- Page {i} ---\n{text}")
        return "\n\n".join(pages_text)

def _try_pypdf2(pdf_path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    pages_text = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text and text.strip():
            pages_text.append(f"--- Page {i} ---\n{text}")
    return "\n\n".join(pages_text)

def _try_pdfminer(pdf_path: str) -> str:
    from pdfminer.high_level import extract_text
    return extract_text(pdf_path)

def _ocr_pdf(pdf_path: str, filename: str) -> Optional[str]:
    """Perform OCR on PDF pages."""
    try:
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(pdf_path, dpi=300)
        ocr_pages = []

        for i, image in enumerate(images, 1):
            text = pytesseract.image_to_string(image, lang='eng')
            if text and text.strip():
                ocr_pages.append(f"--- Page {i} ---\n{text}")

        return "\n\n".join(ocr_pages) if ocr_pages else None
    except ImportError:
        return None
    except Exception:
        return None

def _format_pdf_error(filename: str) -> str:
    return (
        f"[Could not read '{filename}'. This PDF may be:]\n"
        f"• A scanned document (images only, no text)\n"
        f"• Password protected\n"
        f"• Corrupted or malformed\n\n"
        f"Solutions:\n"
        f"1. If scanned: Install OCR support (pip install pytesseract pdf2image)\n"
        f"2. If protected: Remove password before uploading\n"
        f"3. Copy-paste the text directly into chat"
    )

# ==========================================================
# IMAGE PROCESSING
# ==========================================================
def _process_image(content: bytes, filename: str) -> str:
    """Generate caption for image using Hugging Face BLIP."""
    tmp_path = _save_temp_file(content, suffix='.jpg')

    try:
        # 🔥 Validate image with PIL before sending to API
        try:
            from PIL import Image
            with Image.open(tmp_path) as img:
                if img.size[0] < 10 or img.size[1] < 10:
                    return f"[Image: {filename}] - Image is too small to process."
        except ImportError:
            pass  # Skip validation if Pillow not installed

        if not HF_TOKEN:
            return f"[Image: {filename}] - No HF_TOKEN set. Cannot analyze image."

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        # Read and send image to BLIP
        with open(tmp_path, "rb") as f:
            resp = requests.post(HF_API_IMAGE, headers=headers, data=f.read(), timeout=30)

        if resp.status_code != 200:
            return f"[Image analysis failed: HTTP {resp.status_code}]"

        result = resp.json()
        caption = ""

        if isinstance(result, list) and len(result) > 0:
            caption = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            caption = result.get("generated_text", str(result))
        else:
            caption = str(result)

        return f"[Image: {filename}]\nDescription: {caption}" if caption else f"[Image: {filename} - No description]"
    
    except requests.exceptions.Timeout:
        return f"[Image analysis timed out for '{filename}']"
    except requests.exceptions.ConnectionError:
        return f"[Image analysis failed: Could not connect to Hugging Face API]"
    except Exception as e:
        return f"[Could not analyze image '{filename}': {str(e)}]"
    finally:
        _cleanup_temp_file(tmp_path)

# ==========================================================
# OFFICE DOCUMENTS
# ==========================================================
def _process_docx(content: bytes, filename: str) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        texts = [para.text for para in doc.paragraphs if para.text.strip()]
        return f"[Word Document: {filename}]\n\n" + "\n".join(texts)
    except ImportError:
        return "[Word document support requires: pip install python-docx]"
    except Exception as e:
        return f"[Error extracting DOCX: {str(e)}]"

def _process_pptx(content: bytes, filename: str) -> str:
    try:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(content))
        texts = []
        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = [shape.text for shape in slide.shapes if hasattr(shape, "text") and shape.text.strip()]
            if slide_text:
                texts.append(f"[Slide {slide_num}]\n" + "\n".join(slide_text))
        return f"[PowerPoint: {filename}]\n\n" + "\n\n".join(texts)
    except ImportError:
        return "[PowerPoint support requires: pip install python-pptx]"
    except Exception as e:
        return f"[Error extracting PPTX: {str(e)}]"

def _process_excel(content: bytes, filename: str) -> str:
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
        return "[Excel support requires: pip install openpyxl]"
    except Exception as e:
        return f"[Error extracting Excel: {str(e)}]"

# ==========================================================
# TEXT PROCESSING
# ==========================================================
def _process_text(content: bytes, filename: str) -> str:
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            text = content.decode(encoding)
            return f"[File: {filename}]\n\n{text}"
        except UnicodeDecodeError:
            continue
    return f"[Could not decode text file '{filename}'. Unsupported encoding.]"

# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================
def _save_temp_file(content: bytes, suffix: str = '') -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        return tmp.name

def _cleanup_temp_file(path: str) -> None:
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass