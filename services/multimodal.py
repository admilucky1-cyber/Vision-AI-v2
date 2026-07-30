"""
Vision AI v2.0 - Multi-Modal File Processor (multimodal.py)
============================================================
Unified entry point for processing all supported file types.
Handles: PDF (text + OCR), Images (captioning), Text files, Office docs,
Audio (Whisper paid/free), URLs.

Supported formats:
- PDF: pdfplumber -> PyPDF2 -> pdfminer -> OCR (pytesseract)
- Images: JPG, PNG, BMP, WEBP, TIFF (BLIP captioning + OCR fallback)
- Office: DOCX, PPTX, XLSX
- Text: TXT, MD, CSV, JSON, XML, HTML, LOG, PY
- Audio: MP3, WAV, M4A, OGG (Whisper paid/free/local)
- URLs: HTTP/HTTPS (BeautifulSoup scraping)
"""

import os
import io
import tempfile
import traceback
import logging
import re
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# LOGGING SETUP
# ==========================================================
logger = logging.getLogger("vision-ai.multimodal")

# ==========================================================
# CONFIGURATION
# ==========================================================
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_IMAGE = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

# OpenAI Whisper (paid)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Supported file extensions
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'webp', 'tiff', 'tif'}
TEXT_EXTENSIONS = {'txt', 'md', 'csv', 'json', 'xml', 'html', 'log', 'py'}
OFFICE_EXTENSIONS = {'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'}
AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac'}
URL_PATTERN = re.compile(r'^https?://')

# Max file sizes
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_TEXT_LENGTH = 100000  # 100K characters

# ==========================================================
# EXCEPTIONS
# ==========================================================
class FileProcessingError(Exception):
    """Custom exception for file processing failures."""
    pass

class FileTooLargeError(FileProcessingError):
    """Raised when file exceeds size limit."""
    pass

class UnsupportedFileTypeError(FileProcessingError):
    """Raised when file type is not supported."""
    pass

# ==========================================================
# MAIN PROCESSOR (✅ FIXED: SYNCHRONOUS)
# ==========================================================
def process_uploaded_file(file) -> str:
    """
    Process any uploaded file and return text representation.

    Args:
        file: FastAPI UploadFile object

    Returns:
        Extracted text content or error message
    """
    try:
        # Check file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File '{file.filename}' exceeds {MAX_FILE_SIZE//1024//1024}MB limit")

        # ✅ FIX: Use synchronous file read
        content = file.file.read()

        if not content:
            logger.warning(f"File '{file.filename}' is empty")
            return f"[File '{file.filename}' is empty.]"

        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower().lstrip('.')

        logger.info(f"Processing file: {filename} (size: {len(content)} bytes, type: {ext})")

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
        elif ext in AUDIO_EXTENSIONS:
            return _process_audio(content, filename)
        elif re.match(URL_PATTERN, filename):
            # If filename is actually a URL
            return _process_url(content, filename)
        else:
            logger.warning(f"Unsupported file type: .{ext}")
            return f"[Unsupported file type: .{ext}]"

    except FileTooLargeError as e:
        logger.error(f"File too large: {file.filename}")
        return str(e)
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {e}")
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
            logger.info(f"PDF text extracted: {filename} ({len(extracted_text)} chars)")
            return f"[PDF Content - {filename}]\n\n{extracted_text}"

        # Step 2: Try OCR (optional)
        ocr_text = _ocr_pdf(tmp_path, filename)
        if ocr_text and len(ocr_text.strip()) > 50:
            logger.info(f"PDF OCR processed: {filename} ({len(ocr_text)} chars)")
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
        except Exception as e:
            logger.debug(f"PDF extraction method failed: {e}")
            continue
    return None

def _try_pdfplumber(pdf_path: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f"--- Page {i} ---\n{text}")
            return "\n\n".join(pages_text)
    except ImportError:
        raise
    except Exception as e:
        logger.debug(f"pdfplumber failed: {e}")
        raise

def _try_pypdf2(pdf_path: str) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        pages_text = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(f"--- Page {i} ---\n{text}")
        return "\n\n".join(pages_text)
    except ImportError:
        raise
    except Exception as e:
        logger.debug(f"PyPDF2 failed: {e}")
        raise

def _try_pdfminer(pdf_path: str) -> str:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(pdf_path)
    except ImportError:
        raise
    except Exception as e:
        logger.debug(f"pdfminer failed: {e}")
        raise

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
        logger.debug("OCR libraries not installed")
        return None
    except Exception as e:
        logger.debug(f"OCR failed: {e}")
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
        # Validate image with PIL before sending to API
        try:
            from PIL import Image
            with Image.open(tmp_path) as img:
                if img.size[0] < 10 or img.size[1] < 10:
                    return f"[Image: {filename}] - Image is too small to process."
                logger.debug(f"Image dimensions: {img.size}")
        except ImportError:
            logger.debug("Pillow not installed, skipping validation")
        except Exception as e:
            logger.debug(f"Image validation failed: {e}")

        if not HF_TOKEN:
            logger.warning("No HF_TOKEN set for image processing")
            return f"[Image: {filename}] - No HF_TOKEN set. Cannot analyze image."

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        # Read and send image to BLIP
        with open(tmp_path, "rb") as f:
            resp = requests.post(HF_API_IMAGE, headers=headers, data=f.read(), timeout=30)

        if resp.status_code != 200:
            logger.warning(f"Image analysis failed: HTTP {resp.status_code}")
            return f"[Image analysis failed: HTTP {resp.status_code}]"

        result = resp.json()
        caption = ""

        if isinstance(result, list) and len(result) > 0:
            caption = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            caption = result.get("generated_text", str(result))
        else:
            caption = str(result)

        logger.info(f"Image processed: {filename} - Caption: {caption[:50]}...")
        return f"[Image: {filename}]\nDescription: {caption}" if caption else f"[Image: {filename} - No description]"
    
    except requests.exceptions.Timeout:
        logger.error(f"Image analysis timed out for '{filename}'")
        return f"[Image analysis timed out for '{filename}']"
    except requests.exceptions.ConnectionError:
        logger.error(f"Image analysis failed: Could not connect to Hugging Face API")
        return f"[Image analysis failed: Could not connect to Hugging Face API]"
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return f"[Could not analyze image '{filename}': {str(e)}]"
    finally:
        _cleanup_temp_file(tmp_path)

# ==========================================================
# AUDIO PROCESSING (Paid OpenAI + Free HF + Local)
# ==========================================================
def _process_audio(content: bytes, filename: str) -> str:
    """
    Transcribe audio using Whisper.
    Priority:
    1. OpenAI API (paid, best quality)
    2. Hugging Face API (free, good quality)
    3. Local Whisper (free, offline)
    """
    tmp_path = _save_temp_file(content, suffix='.mp3')

    try:
        # Option 1: OpenAI Whisper (paid)
        if OPENAI_API_KEY:
            try:
                logger.info(f"Using OpenAI Whisper (paid) for {filename}")
                import openai
                openai.api_key = OPENAI_API_KEY
                with open(tmp_path, "rb") as f:
                    response = openai.Audio.transcribe(
                        model="whisper-1",
                        file=f
                    )
                text = response.get("text", "").strip()
                if text:
                    logger.info(f"OpenAI Whisper transcribed: {filename} ({len(text)} chars)")
                    return f"[Audio Transcription (OpenAI): {filename}]\n\n{text}"
            except Exception as e:
                logger.warning(f"OpenAI Whisper failed: {e}. Falling back to HF/local.")

        # Option 2: Hugging Face Whisper (free)
        if HF_TOKEN:
            try:
                logger.info(f"Using Hugging Face Whisper (free) for {filename}")
                import requests
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                with open(tmp_path, "rb") as f:
                    resp = requests.post(
                        "https://api-inference.huggingface.co/models/openai/whisper-large-v3",
                        headers=headers,
                        data=f.read(),
                        timeout=60
                    )
                if resp.status_code == 200:
                    result = resp.json()
                    text = result.get("text", "").strip()
                    if text:
                        logger.info(f"HF Whisper transcribed: {filename} ({len(text)} chars)")
                        return f"[Audio Transcription (Hugging Face): {filename}]\n\n{text}"
                else:
                    logger.warning(f"HF Whisper returned {resp.status_code}. Falling back to local.")
            except Exception as e:
                logger.warning(f"HF Whisper failed: {e}. Falling back to local.")

        # Option 3: Local Whisper (free, offline)
        try:
            logger.info(f"Using local Whisper (free, offline) for {filename}")
            import whisper
            model = whisper.load_model("base")  # Use "tiny" for speed, "large" for accuracy
            result = model.transcribe(tmp_path)
            text = result.get("text", "").strip()
            if text:
                logger.info(f"Local Whisper transcribed: {filename} ({len(text)} chars)")
                return f"[Audio Transcription (Local): {filename}]\n\n{text}"
        except ImportError:
            logger.warning("Local Whisper not installed. Skipping.")
        except Exception as e:
            logger.warning(f"Local Whisper failed: {e}")

        # If all fail
        return f"[Could not transcribe audio '{filename}'. No Whisper model available.]"

    finally:
        _cleanup_temp_file(tmp_path)

# ==========================================================
# URL PROCESSING
# ==========================================================
def _process_url(content: bytes, filename: str) -> str:
    """Fetch and extract text from a URL."""
    try:
        from bs4 import BeautifulSoup
        url = content.decode('utf-8').strip()
        if not url.startswith(('http://', 'https://')):
            return f"[Invalid URL: {url}]"
        
        headers = {"User-Agent": "VisionAI/2.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()
        
        title = soup.title.string if soup.title else "No title"
        text = soup.get_text()[:10000]  # Limit to 10K chars
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return f"[URL: {url}]\nTitle: {title}\n\n{text}"
    except ImportError:
        return "[URL fetching requires: pip install beautifulsoup4]"
    except Exception as e:
        return f"[Error fetching URL: {str(e)}]"

# ==========================================================
# OFFICE DOCUMENTS
# ==========================================================
def _process_docx(content: bytes, filename: str) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        texts = [para.text for para in doc.paragraphs if para.text.strip()]
        logger.info(f"DOCX processed: {filename} ({len(texts)} paragraphs)")
        return f"[Word Document: {filename}]\n\n" + "\n".join(texts)
    except ImportError:
        logger.warning("python-docx not installed")
        return "[Word document support requires: pip install python-docx]"
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
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
        logger.info(f"PPTX processed: {filename} ({len(texts)} slides)")
        return f"[PowerPoint: {filename}]\n\n" + "\n\n".join(texts)
    except ImportError:
        logger.warning("python-pptx not installed")
        return "[PowerPoint support requires: pip install python-pptx]"
    except Exception as e:
        logger.error(f"PPTX extraction error: {e}")
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
        logger.info(f"Excel processed: {filename} ({len(texts)} sheets)")
        return f"[Excel: {filename}]\n\n" + "\n\n".join(texts)
    except ImportError:
        logger.warning("openpyxl not installed")
        return "[Excel support requires: pip install openpyxl]"
    except Exception as e:
        logger.error(f"Excel extraction error: {e}")
        return f"[Error extracting Excel: {str(e)}]"

# ==========================================================
# TEXT PROCESSING
# ==========================================================
def _process_text(content: bytes, filename: str) -> str:
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            text = content.decode(encoding)
            # Truncate if too long
            if len(text) > MAX_TEXT_LENGTH:
                text = text[:MAX_TEXT_LENGTH] + "\n\n[Text truncated due to length]"
            logger.info(f"Text file processed: {filename} ({len(text)} chars)")
            return f"[File: {filename}]\n\n{text}"
        except UnicodeDecodeError:
            continue
    logger.warning(f"Could not decode text file: {filename}")
    return f"[Could not decode text file '{filename}'. Unsupported encoding.]"

# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================
def _save_temp_file(content: bytes, suffix: str = '') -> str:
    """Save content to a temporary file and return path."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
        logger.debug(f"Temporary file created: {tmp_path}")
        return tmp_path

def _cleanup_temp_file(path: str) -> None:
    """Remove temporary file if it exists."""
    try:
        if os.path.exists(path):
            os.unlink(path)
            logger.debug(f"Temporary file removed: {path}")
    except Exception as e:
        logger.warning(f"Failed to remove temporary file {path}: {e}")

def check_file_size(content: bytes, max_size: int = MAX_FILE_SIZE) -> bool:
    """Check if file size is within limits."""
    return len(content) <= max_size

def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower().lstrip('.')

# ==========================================================
# EXPORTS
# ==========================================================
__all__ = [
    "process_uploaded_file",
    "FileProcessingError",
    "FileTooLargeError",
    "UnsupportedFileTypeError",
    "check_file_size",
    "get_file_extension",
]

logger.info("👁️ Vision AI Multi-Modal Processor v2.0 - Ready")