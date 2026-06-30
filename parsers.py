import json
import io
import re
import PyPDF2

def parse_resume_pdf(file_bytes: bytes) -> dict:
    """
    Extracts text from PDF and mocks a basic dictionary extraction.
    For high accuracy, replace this regex logic with an LLM call.
    """
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
        
    # Basic Regex heuristics for demonstration
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    phones = re.findall(r'\(?\+?[0-9]*\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', text)
    
    raw_data = {
        "candidate_name": text.split('\n')[0] if text else "",
        "contact_emails": emails,
        "phone_num": phones[0] if phones else "",
        "raw_text": text
    }
    return raw_data

def parse_ats_json(file_bytes: bytes) -> dict:
    """Parses raw ATS JSON blobs."""
    try:
        data = json.loads(file_bytes.decode('utf-8'))
        return data
    except json.JSONDecodeError:
        return {}