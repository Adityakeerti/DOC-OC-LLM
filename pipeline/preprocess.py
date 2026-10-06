"""
preprocess.py — Prepare marksheet images for VLM extraction.

Handles three things:
  1. PDF → JPG conversion (renders first page at high resolution)
  2. EXIF auto-orientation (fixes rotated phone photos)
  3. Proportional resize (max 1600px, keeps text sharp)

No destructive operations — no cropping, no color changes, no filters.
The VLM works best with the original, clean image.
"""

import io
from pathlib import Path
from PIL import Image, ImageOps


# ── Config ────────────────────────────────────────────────────────────────────

MAX_DIMENSION = 1600  # High-fidelity trade-off: preserves small text and double digits with crisp patches


# ── PDF Handling ──────────────────────────────────────────────────────────────

def pdf_to_image(pdf_path: str) -> Image.Image:
    """Render the first page of a PDF as a high-resolution image."""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    page = doc.load_page(0)

    # 2.5x matrix (~180-200 DPI) for crisp character strokes on scanned marksheets
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
    img_bytes = pixmap.tobytes("ppm")
    doc.close()

    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


# ── Image Loading ─────────────────────────────────────────────────────────────

def load_image(path: str) -> Image.Image:
    """Load any supported file (JPG, PNG, PDF) as a PIL Image."""
    if path.lower().endswith(".pdf"):
        return pdf_to_image(path)

    image = Image.open(path)
    image = ImageOps.exif_transpose(image)  # Fix phone camera rotation
    return image.convert("RGB")


# ── Resizing ──────────────────────────────────────────────────────────────────

def resize(image: Image.Image, max_dim: int = MAX_DIMENSION) -> Image.Image:
    """Shrink image proportionally so the largest side ≤ max_dim pixels."""
    width, height = image.size

    # Already small enough — return as-is
    if max(width, height) <= max_dim:
        return image

    scale = max_dim / max(width, height)
    new_size = (int(width * scale), int(height * scale))

    return image.resize(new_size, Image.LANCZOS)


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def prepare(path: str) -> Image.Image:
    """
    Full preprocessing: load file → fix orientation → resize.

    Args:
        path: Path to image (JPG/PNG) or PDF file

    Returns:
        Clean PIL Image ready for VLM extraction
    """
    image = load_image(path)
    image = resize(image)
    return image
