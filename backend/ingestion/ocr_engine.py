import io
import asyncio
import pymupdf as fitz
import pytesseract
from PIL import Image
from backend.config.settings import TESSERACT_CMD

# Configure Tesseract binary path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def run_tesseract_ocr(img: Image.Image) -> str:
    """Performs Tesseract OCR on a PIL Image object."""
    return pytesseract.image_to_string(img)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF document page-by-page using PyMuPDF (fitz).
    If page text contains less than 50 characters, triggers Tesseract OCR fallback.
    """
    doc = fitz.open(pdf_path)
    combined_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()

        if len(text) < 50:
            pix = page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = run_tesseract_ocr(img)
            combined_text.append(f"--- Page {page_num + 1} (OCR) ---\n{text}")
        else:
            combined_text.append(f"--- Page {page_num + 1} (Native) ---\n{text}")

    doc.close()
    return "\n".join(combined_text)

async def extract_text_from_pdf_async(pdf_path: str) -> str:
    """Async wrapper to offload CPU-intensive OCR and PDF parsing."""
    return await asyncio.to_thread(extract_text_from_pdf, pdf_path)
