import fitz
import pdfplumber
from docx import Document
import subprocess
import platform
import os
import re
from PIL import Image
import io
import pytesseract

def extract_fitz_advanced(path):
    text = ""
    fraud_flags = []
    try:
        doc = fitz.open(path)
        if doc.needs_pass:
            doc.authenticate("")
            
        white_char_count = 0
        total_char_count = 0
        for page in doc:
            page_data = page.get_text("dict", sort=True)
            for block in page_data.get("blocks", []):
                if block.get("type") != 0: continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        chars = len(span.get("text", "").strip())
                        total_char_count += chars
                        if span.get("color") == 16777215:
                            white_char_count += chars
                            
        is_dark_mode = total_char_count > 0 and (white_char_count / total_char_count) > 0.04

        for page in doc:
            page_data = page.get_text("dict", sort=True)
            for block in page_data.get("blocks", []):
                if block.get("type") != 0: continue
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("color") == 16777215 and not is_dark_mode:
                            if "invisible_text" not in fraud_flags: fraud_flags.append("invisible_text")
                            continue 
                        if span.get("size", 10) < 4.0:
                            if "microscopic_text" not in fraud_flags: fraud_flags.append("microscopic_text")
                            continue 
                        block_text += span.get("text", "") + " "
                    block_text += "\n"
                text += block_text.strip() + "\n\n"
    except Exception as e:
        print("PyMuPDF advanced extraction failed:", e)
        return "", []
    return text.strip(), fraud_flags


def extract_pdfplumber(path):
    text = ""
    try:
        with pdfplumber.open(path, password="") as pdf:
            for page in pdf.pages:
                text += page.extract_text(layout=True) or ""
    except Exception as e:
        print("pdfplumber failed:", e)
    return text, []


def extract_ocr_tesseract(path):
    """
    Enterprise-Grade C++ Tesseract OCR Fallback.
    Lightning fast image-to-text conversion for locked/Canva PDFs.
    """
    print(f"Triggering Enterprise Tesseract OCR for {path}...")
    text = ""
    try:
        doc = fitz.open(path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Matrix(3, 3) scales the PDF up to ~216 DPI
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            
            # Render directly to PIL Image in memory
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # Tesseract extraction
            text += pytesseract.image_to_string(img) + "\n"
            
    except Exception as e:
        print("Tesseract OCR failed:", e)
    return text, []


def extract_docx(path):
    text = ""
    try:
        doc = Document(path)
        for para in doc.paragraphs: text += para.text + "\n"
    except Exception as e:
        print("docx failed:", e)
    return text, []


def extract_doc(path):
    text = ""
    system = platform.system()
    try:
        if system == "Darwin": 
            result = subprocess.run(['textutil', '-stdout', '-cat', 'txt', path], capture_output=True, text=True, check=True)
            text = result.stdout
        elif system == "Windows":
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(os.path.abspath(path))
            text = doc.Content.Text
            doc.Close()
            word.Quit()
        else:
            result = subprocess.run(['antiword', path], capture_output=True, text=True, check=True)
            text = result.stdout
    except Exception as e:
        with open(path, 'rb') as f: raw_data = f.read()
        text = " ".join(re.findall(rb'[a-zA-Z0-9.,;:!? \n\t]{4,}', raw_data).decode('utf-8', errors='ignore'))
    return text, []


def extract_text(path):
    """
    Master router for file ingestion with a True Waterfall 3-Tier fallback system.
    Evaluates success based purely on alphabetical character yield.
    """
    ext = path.lower()
    text = ""
    fraud_flags = []
    
    if ext.endswith(".pdf"):
        # TIER 1: Advanced PyMuPDF
        text, fraud_flags = extract_fitz_advanced(path)
        best_alpha = len(re.sub(r'[^a-zA-Z]', '', text))
        
        # TIER 2: Plumber Fallback (If text is missing or scrambled gibberish)
        if best_alpha < 200:
            print(f"Low semantic yield from PyMuPDF for {path}. Trying pdfplumber...")
            fallback_text, _ = extract_pdfplumber(path)
            fallback_alpha = len(re.sub(r'[^a-zA-Z]', '', fallback_text))
            
            if fallback_alpha > best_alpha:
                text = fallback_text
                best_alpha = fallback_alpha
                fraud_flags = [] 
                
        # TIER 3: Tesseract OCR Fallback (For Scanned/Locked Images like Abhishek's)
        if best_alpha < 200:
            print(f"Text layer still missing/corrupted in {path}. Triggering Tesseract OCR...")
            ocr_text, _ = extract_ocr_tesseract(path)
            ocr_alpha = len(re.sub(r'[^a-zA-Z]', '', ocr_text))
            
            if ocr_alpha > best_alpha:
                text = ocr_text
                fraud_flags = [] 

    elif ext.endswith(".docx"):
        text, fraud_flags = extract_docx(path)
    elif ext.endswith(".doc"):
        text, fraud_flags = extract_doc(path)
    else:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception:
            raise ValueError(f"Unsupported file type: {path}")

    return {
        "raw_text": text,
        "fraud_flags": fraud_flags
    }