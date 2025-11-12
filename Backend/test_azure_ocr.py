import os
import requests
import time
from dotenv import load_dotenv

# Load API credentials
load_dotenv()
endpoint = os.getenv("AZURE_OCR_ENDPOINT")
key = os.getenv("AZURE_OCR_KEY")

# OCR API endpoint (this is the "Read" API)
ocr_url = endpoint + "vision/v3.2/read/analyze"

# Choose a test image file (replace with your local path)
image_path = r"C:\Users\Shour\OneDrive\Desktop\On_Track\ML Resources\ML\End-End\Expense_TrackerFolder\Backend\test_reciept.png"

with open(image_path, "rb") as f:
    image_data = f.read()

headers = {
    "Ocp-Apim-Subscription-Key": key,
    "Content-Type": "application/octet-stream",
}

# Step 1: Send image for OCR
print("Submitting image to Azure OCR...")
response = requests.post(ocr_url, headers=headers, data=image_data)
response.raise_for_status()

# Step 2: Poll for results
operation_url = response.headers["Operation-Location"]
print("Operation URL:", operation_url)

while True:
    result = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": key})
    result_json = result.json()
    status = result_json.get("status")

    if status == "succeeded":
        break
    elif status == "failed":
        raise Exception("OCR failed.")
    time.sleep(1)

# Step 3: Extract text
print("\n--- OCR Output ---\n")
for page in result_json["analyzeResult"]["readResults"]:
    for line in page["lines"]:
        print(line["text"])


