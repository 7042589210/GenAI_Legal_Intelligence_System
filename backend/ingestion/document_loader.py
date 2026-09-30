import docx2txt
import asyncio
from backend.ingestion.ocr_engine import extract_text_from_pdf, extract_text_from_pdf_async, run_tesseract_ocr
from PIL import Image

def extract_text_from_file(file_path: str) -> str:
    """Dispatches document to appropriate parser based on file extension."""
    lower_path = file_path.lower()
    if lower_path.endswith('.docx'):
        return docx2txt.process(file_path)
    elif lower_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif lower_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif lower_path.endswith(('.jpg', '.jpeg', '.png')):
        img = Image.open(file_path)
        return run_tesseract_ocr(img)
    else:
        raise ValueError("Unsupported file format. Only PDF, DOCX, TXT, and Images are allowed.")

async def extract_text_from_file_async(file_path: str) -> str:
    """Async dispatch for document extraction to offload CPU-bound tasks."""
    lower_path = file_path.lower()
    if lower_path.endswith('.pdf'):
        return await extract_text_from_pdf_async(file_path)
    elif lower_path.endswith('.docx'):
        return await asyncio.to_thread(docx2txt.process, file_path)
    elif lower_path.endswith('.txt'):
        def _read_txt():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return await asyncio.to_thread(_read_txt)
    elif lower_path.endswith(('.jpg', '.jpeg', '.png')):
        def _read_img():
            img = Image.open(file_path)
            return run_tesseract_ocr(img)
        return await asyncio.to_thread(_read_img)
    else:
        raise ValueError("Unsupported file format. Only PDF, DOCX, TXT, and Images are allowed.")
