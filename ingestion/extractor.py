import fitz
import pdfplumber
from docx import Document


def extract_fitz(path):
    text = ""

    try:
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()

    except Exception as e:
        print("PyMuPDF failed:", e)

    return text


def extract_pdfplumber(path):
    text = ""

    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    except Exception as e:
        print("pdfplumber failed:", e)

    return text


def extract_docx(path):
    text = ""

    try:
        doc = Document(path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    except Exception as e:
        print("docx failed:", e)

    return text


def extract_text(path):
    if path.endswith(".pdf"):
        text = extract_fitz(path)

        if len(text.strip()) < 500:
            print("Fallback to pdfplumber")
            text = extract_pdfplumber(path)

    elif path.endswith(".docx"):
        text = extract_docx(path)

    else:
        raise ValueError("Unsupported file type")

    return text
