# Backend/services/azure_ocr.py

import os
import time
import requests
from dotenv import load_dotenv

# ------------------------------------------------------
# ✅ Load credentials from .env (one level above /services)
# ------------------------------------------------------
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

AZURE_OCR_KEY = os.getenv("AZURE_OCR_KEY")
AZURE_OCR_ENDPOINT = os.getenv("AZURE_OCR_ENDPOINT")

# Debug check (optional)
if not AZURE_OCR_KEY or not AZURE_OCR_ENDPOINT:
    print("[ERROR] ❌ Azure OCR key or endpoint not loaded. Check .env path:", env_path)
else:
    print("[DEBUG] ✅ Azure credentials loaded successfully from:", env_path)


def extract_text_from_file(file):
    """
    Send a receipt image or PDF file to Azure OCR (Computer Vision Read API)
    and return the extracted text as a single string.
    """
    if not AZURE_OCR_KEY or not AZURE_OCR_ENDPOINT:
        raise ValueError("Azure OCR key or endpoint not found. Check your .env file.")

    # Azure 'Read' endpoint for OCR
    analyze_url = f"{AZURE_OCR_ENDPOINT}vision/v3.2/read/analyze"

    # Read the uploaded file's bytes
    file_data = file.file.read()

    # Set request headers
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_OCR_KEY,
        "Content-Type": "application/octet-stream",
    }

    # Step 1: Submit the file to Azure for OCR analysis
    response = requests.post(analyze_url, headers=headers, data=file_data)
    response.raise_for_status()

    # Step 2: Retrieve the operation URL to poll results
    operation_url = response.headers.get("Operation-Location")
    if not operation_url:
        raise Exception("Azure OCR response missing Operation-Location header.")

    # Step 3: Poll until results are ready
    while True:
        result = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": AZURE_OCR_KEY})
        result_json = result.json()
        status = result_json.get("status")

        if status == "succeeded":
            break
        elif status == "failed":
            raise Exception("Azure OCR processing failed.")
        time.sleep(1)

    # Step 4: Extract all recognized text lines
    lines = []
    try:
        for read_result in result_json["analyzeResult"]["readResults"]:
            for line in read_result["lines"]:
                lines.append(line["text"])
    except KeyError:
        raise Exception("Unexpected response format from Azure OCR.")

    # Step 5: Return the recognized text
    return "\n".join(lines)
