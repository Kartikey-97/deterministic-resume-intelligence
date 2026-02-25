import re
import unicodedata

def clean_text(text: str) -> str:
    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Remove zero-width characters
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

    # Remove encoding junk
    text = text.replace("\xa0", " ")
    text = text.replace("Â", " ")

    # Remove weird fraction-like garbage
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    # Remove control characters but keep newlines
    text = re.sub(r"[\x00-\x09\x0B-\x1F\x7F]", "", text)

    # Normalize line breaks
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)

    # Normalize spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize bullets and separators
    text = re.sub(r"[•·▪►q]", " ", text)
    text = re.sub(r"[ï¼​]", " ", text)

    return text.strip()