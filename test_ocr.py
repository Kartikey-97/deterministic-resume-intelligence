import fitz
from PIL import Image
import io
import pytesseract
import time
import os

def test_fast_ocr(pdf_path):
    print(f"\n[+] Starting Enterprise Tesseract OCR on: {pdf_path}")
    start_time = time.time()
    text = ""

    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            print(f" -> Scanning Page {page_num + 1}...")
            
            # THE FIX: Actually load the page into memory!
            page = doc.load_page(page_num)
            
            # Matrix(3, 3) scales the PDF up to ~216 DPI (Perfect for Tesseract accuracy)
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            
            # Render directly to PIL Image in memory (Bypasses Poppler completely!)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # Tesseract C++ engine extracts text in ~1-2 seconds
            page_text = pytesseract.image_to_string(img)
            text += page_text + "\n"
            
        end_time = time.time()
        print(f"\n[SUCCESS] OCR Complete in {end_time - start_time:.2f} seconds!\n")
        print("="*50)
        print("EXTRACTED TEXT PAYLOAD:")
        print("="*50)
        print(text.strip())
        print("="*50)

    except Exception as e:
        print(f"\n[ERROR] OCR Failed: {e}")

if __name__ == "__main__":
    # Updated to the correct filename
    target_file = "ResumeABHISHEKKUMARKumar1.pdf" 
    
    if os.path.exists(target_file):
        test_fast_ocr(target_file)
    else:
        print(f"Error: Could not find '{target_file}' in the current folder.")