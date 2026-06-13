"""OCR ingestion (roadmap §3) — widen what the agent can ground on to scanned/legacy PDFs & images.

The engine already extracts text from *digital* documents (`textextract.py` / pypdf). This module adds a
**digital-first** extractor with an **OCR fallback** for image-only pages:
  * digital text present              -> use it (no OCR, no cost),
  * little/no text + OCR available    -> OCR the page images,
  * OCR backend not installed/failed  -> a clear, graceful result (never crashes the pipeline).

OCR backends are **optional** — never required for the core POC:
  * Production: **Azure AI Document Intelligence** (in-tenant; strong on tables/forms — rate sheets, bid forms).
  * Local/dev:  **Tesseract** via `pip install -e ".[ocr]"` (pytesseract + pdf2image + Pillow) + the
                Tesseract binary. Without it, the digital path still works.

Guardrail: OCR text feeds **grounding only** — it never bypasses the human approval / validation gates.
"""
from __future__ import annotations

from pathlib import Path

MIN_DIGITAL_CHARS = 40   # below this, treat a PDF/image as image-only and try OCR
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def ocr_available() -> bool:
    """True only if a local OCR backend (Tesseract via pytesseract + pdf2image) is importable."""
    try:
        import pytesseract  # noqa: F401
        from pdf2image import convert_from_path  # noqa: F401
        return True
    except Exception:
        return False


def _digital_text(path: Path) -> str:
    from .textextract import extract_text
    try:
        return (extract_text(str(path)) or "").strip()
    except Exception:
        return ""


def _ocr_text(path: Path) -> str:
    import pytesseract
    if path.suffix.lower() == ".pdf":
        from pdf2image import convert_from_path
        return "\n".join(pytesseract.image_to_string(p) for p in convert_from_path(str(path))).strip()
    from PIL import Image
    return pytesseract.image_to_string(Image.open(path)).strip()


def extract_document_text(path) -> tuple[str, str]:
    """Return ``(text, method)``; method ∈ {'digital', 'ocr', 'ocr-unavailable', 'empty'}.

    Never raises on a bad/scanned file — the worst case is empty text with an explanatory method.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {".docx", ".pptx", ".xlsx"}:
        return _digital_text(path), "digital"

    digital = _digital_text(path) if suffix == ".pdf" else ""
    if len(digital) >= MIN_DIGITAL_CHARS:
        return digital, "digital"

    if suffix == ".pdf" or suffix in _IMAGE_SUFFIXES:
        if ocr_available():
            try:
                text = _ocr_text(path)
            except Exception:
                return "", "empty"
            return (text, "ocr") if text else ("", "empty")
        return digital, "ocr-unavailable"

    return digital, ("digital" if digital else "empty")
