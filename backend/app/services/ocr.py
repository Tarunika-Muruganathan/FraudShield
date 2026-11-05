import io
import os
from pathlib import Path
import shutil

import fitz  # PyMuPDF
from PIL import Image, ImageOps
import pytesseract


def configure_tesseract():
    """Locates and configures the Tesseract OCR binary path across common installations."""
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd and Path(env_cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = env_cmd
        return

    candidate_paths = [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")),
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for candidate in candidate_paths:
        if candidate.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return

    # Check system PATH
    system_tess = shutil.which("tesseract")
    if system_tess:
        pytesseract.pytesseract.tesseract_cmd = system_tess


# Initialize configuration on import
configure_tesseract()


class OcrProcessingError(Exception):
    """Raised when document OCR or reading fails."""
    pass


def extract_text_from_image(file_path: Path) -> str:
    """Extracts text from PNG, JPG, or JPEG image using PIL and Tesseract."""
    try:
        with Image.open(file_path) as img:
            # Handle orientation if EXIF present
            img = ImageOps.exif_transpose(img)
            # Convert to RGB mode for OCR consistency
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            text = pytesseract.image_to_string(img, lang="eng")
            return text.strip()
    except Exception as e:
        raise OcrProcessingError(f"Image OCR failed: {str(e)}")


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extracts text from PDF documents using PyMuPDF.
    If native text is absent (e.g., scanned PDF), renders pages to images and runs Tesseract OCR.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise OcrProcessingError(f"Invalid or corrupted PDF file: {str(e)}")

    extracted_pages = []

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            # First attempt native text extraction
            native_text = page.get_text().strip()

            if len(native_text) >= 25:
                extracted_pages.append(native_text)
            else:
                # Scanned or image-based PDF page -> Render to pixmap and run Tesseract OCR
                try:
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    with Image.open(io.BytesIO(img_bytes)) as img:
                        ocr_text = pytesseract.image_to_string(img, lang="eng")
                        if ocr_text.strip():
                            extracted_pages.append(ocr_text.strip())
                        elif native_text:
                            extracted_pages.append(native_text)
                except Exception as page_err:
                    # If single page OCR fails, keep any native text
                    if native_text:
                        extracted_pages.append(native_text)
                    else:
                        raise OcrProcessingError(f"Failed to OCR PDF page {page_num + 1}: {str(page_err)}")

        full_text = "\n\n--- Page Break ---\n\n".join(extracted_pages).strip()
        return full_text
    finally:
        doc.close()


def process_document_ocr(file_path: Path, filename: str) -> str:
    """
    Dispatches file to the appropriate OCR pipeline based on extension.
    Returns extracted raw text.
    """
    if not file_path.is_file():
        raise OcrProcessingError(f"Evidence file not found on disk at {file_path}")

    ext = Path(filename).suffix.lower()

    if ext in (".png", ".jpg", ".jpeg"):
        return extract_text_from_image(file_path)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        raise OcrProcessingError(f"Unsupported file format '{ext}' for OCR processing.")

