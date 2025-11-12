# Backend/routes/ocr.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from Expense_TrackerFolder.Backend.services.azure_ocr import extract_text_from_file
from Expense_TrackerFolder.Backend.services.extract_fields import parse_expense_fields

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """
    Upload a receipt (image or PDF), extract text using Azure OCR,
    then parse date, amount, item name, and category.
    """
    try:
        ocr_text = extract_text_from_file(file)
        parsed = parse_expense_fields(ocr_text)
        return {
            "success": True,
            "parsed": parsed,
            "raw_text": ocr_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")
