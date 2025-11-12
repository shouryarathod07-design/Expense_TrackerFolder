from dotenv import load_dotenv
import os

load_dotenv()

print("AZURE_OCR_ENDPOINT =", os.getenv("AZURE_OCR_ENDPOINT"))
print("AZURE_OCR_KEY =", os.getenv("AZURE_OCR_KEY")[:5] + "********")
