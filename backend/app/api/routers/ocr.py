"""Receipt OCR endpoint: returns a prefill suggestion; never writes expenses."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from datetime import date

from app.api.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import OCRResult
from app.services.ocr import extract_receipt_fields

router = APIRouter(prefix="/ocr", tags=["ocr"])

MAX_BYTES = 8 * 1024 * 1024


@router.post("/receipt", response_model=OCRResult)
async def scan_receipt(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image too large (max 8 MB)")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(415, "Upload an image file")
    result = extract_receipt_fields(data, mime_type=file.content_type or "image/jpeg")
    if isinstance(result.get("date"), str):
        try:
            result["date"] = date.fromisoformat(result["date"][:10])
        except ValueError:
            result["date"] = None
    return OCRResult(**result)
