"""
Document parsing: extract text from PDF, images, docs.
"""

import io


async def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file. Requires PyPDF2 or similar."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except ImportError:
        return "[PDF parsing requires PyPDF2 - install with: pip install PyPDF2]"
    except Exception as e:
        return f"[Error parsing PDF: {e}]"


async def extract_text_from_image(file_bytes: bytes) -> str:
    """Extract text from an image using OCR. Requires pytesseract."""
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image).strip()
    except ImportError:
        return "[Image OCR requires pytesseract and Pillow]"
    except Exception as e:
        return f"[Error parsing image: {e}]"


async def extract_text(file_bytes: bytes, content_type: str) -> str:
    """Route to appropriate parser based on content type."""
    if "pdf" in content_type:
        return await extract_text_from_pdf(file_bytes)
    elif "image" in content_type:
        return await extract_text_from_image(file_bytes)
    else:
        # Try to decode as text
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            return "[Unsupported file format]"
