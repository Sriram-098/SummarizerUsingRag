"""
OCR Module — Extract text from scanned PDFs and images.
Uses Tesseract OCR via pytesseract + pdf2image.
"""
import os
import tempfile
from typing import Optional


def is_tesseract_available() -> bool:
    """Check if Tesseract OCR is installed on the system."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_pdf(pdf_path: str) -> str:
    """
    Extract text from a scanned PDF using OCR.
    Converts each page to an image, then runs Tesseract on each.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text string.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        raise RuntimeError(
            "OCR dependencies not installed. "
            "Install with: pip install pytesseract pdf2image Pillow"
        )

    if not is_tesseract_available():
        raise RuntimeError(
            "Tesseract OCR is not installed or not in PATH.\n"
            "Install: https://github.com/tesseract-ocr/tesseract\n"
            "Windows: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    pages = convert_from_path(pdf_path, dpi=300)
    text_parts = []
    for i, page in enumerate(pages):
        page_text = pytesseract.image_to_string(page, lang="eng")
        text_parts.append(f"--- Page {i + 1} ---\n{page_text}")

    return "\n\n".join(text_parts)


def ocr_image(image_path: str) -> str:
    """Extract text from a single image using OCR."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise RuntimeError("OCR dependencies not installed.")

    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang="eng")


def extract_text_with_ocr(file_path: str) -> Optional[str]:
    """
    Smart extraction: try regular text first, fall back to OCR.
    Returns extracted text, or None if extraction fails.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        # Try regular extraction first
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text

            # If very little text extracted, it's probably scanned → OCR
            if len(text.strip()) < 50:
                print(f"[OCR] Low text yield ({len(text)} chars), using OCR...")
                return ocr_pdf(file_path)
            return text
        except Exception:
            return ocr_pdf(file_path)

    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return ocr_image(file_path)

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    return None
