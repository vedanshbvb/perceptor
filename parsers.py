import json
import io
import os
import PyPDF2
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables (Make sure you have a .env file with GEMINI_API_KEY)
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize the client
client = genai.Client(api_key=api_key)

def verify_no_hallucinations(parsed_json: dict, raw_text: str) -> dict:
    """
    Checks key extracted entities against the raw resume text. 
    Drops the tuple if the primary entity (Company, Institution, or Skill) 
    isn't found anywhere in the text.
    """
    text_lower = raw_text.lower()
    
    def check_exists(val: str) -> bool:
        if not val: 
            return True # Don't drop if empty, just ignore
        return val.lower() in text_lower

    # Verify Experiences (Drop if Company is missing)
    if "experiences" in parsed_json:
        valid_exps = []
        for exp in parsed_json["experiences"]:
            # exp index 0 is company
            if len(exp) > 0 and check_exists(str(exp[0])):
                valid_exps.append(exp)
        parsed_json["experiences"] = valid_exps

    # Verify Education (Drop if Institution is missing)
    if "education" in parsed_json:
        valid_edu = []
        for edu in parsed_json["education"]:
            # edu index 0 is institution
            if len(edu) > 0 and check_exists(str(edu[0])):
                valid_edu.append(edu)
        parsed_json["education"] = valid_edu
        
    # Verify Skills (Drop if Skillname is missing)
    if "skills" in parsed_json:
        valid_skills = []
        for skill in parsed_json["skills"]:
            # skill index 0 is skillname
            if len(skill) > 0 and check_exists(str(skill[0])):
                valid_skills.append(skill)
        parsed_json["skills"] = valid_skills

    return parsed_json

def parse_resume_pdf(file_bytes: bytes) -> dict:
    """
    Extracts text from PDF and uses Gemini to parse it into structured JSON.
    """
    # 1. Extract text from the PDF
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
            
    # 2. Prepare the Prompt with your specific rules
    prompt = f"""
    You are an expert ATS data extraction system. Extract information from the following resume text and format it STRICTLY as JSON.
    Follow these rules:
    1. Dates must be in YYYY-MM-DD format. If only month and year are given, use 01 for the day.
    2. Phone numbers must follow the E.164 standard international format. For example- +919876543210
    3. Write names of institutions and companies in their origninal form, the way they were given (e.g., if the resume had 'Indian Institute of Technology Delhi' then write that, if it had 'IITD' then write 'IITD').
    4. The provenance field must be a list of arrays. For every key you populate, add an array formatted as ["field_name", "resume", "llm"].
    5. If there is no information for some field of the schema, just leave that field empty.
    6. For the summary part of the experience, keep it exactly same as what is mentioned in the resume.
    7. For the rating of the skill, always keep it as 8.
    8. Do NOT make up information by yourself and do NOT hallucinate

    Required JSON Schema:
    {{
      "full_name": "string",
      "emails": ["string"],
      "phone": "string",
      "curr_location": ["city", "region", "country"],
      "links": ["leetcode link", "github link", "portfolio link", ["other links", "other links"]],
      "yoe": number,
      "skills": [
        ["skillname", rating_out_of_10, ["source1", "source2"]]
      ],
      "experiences": [
        ["company", "title", "YYYY-MM-DD", "YYYY-MM-DD", "summary"]
      ],
      "education": [
        ["institution", "degree", "field", end_year_number]
      ],
      "certifications": ["string"],
      "provenance": [
        ["field_name", "source", "method"]
      ]
    }}

    Example:
    {{
      "full_name": "Rohan Jain",
      "emails": ["rohan@gmail.com"],
      "phone": "+911234567890",
      "curr_location": ["Bangalore", "Karnataka", "India"],
      "links": ["", "https://github.com/rohan", "", ["https://blogspot.com/rohanblogs", "https://codeforces.com/rohan"]],
      "yoe": 1,
      "skills": [
        ["Python", 8, ["Google", "Meta"]]
      ],
      "experiences": [
        ["Google", "SDE1", "2026-03-01", "2026-05-01", "Worked on error handling"], ["Meta", "ML Engineer", "2025-07-12", "2026-02-28", "Made foundation model for meta glasses"]
      ],
      "education": [
        ["IIT Bh", "B.Tech", "Computer Science", 2024]
      ],
      "certifications": [""],
      "provenance": [
        ["full_name", "resume", "llm"],
        ["emails", "resume", "llm"],
        ["phone", "resume", "llm"],
        ["curr_location", "resume", "llm"],
        ["links", "resume", "llm"],
        ["yoe", "resume", "llm"],
        ["skills", "resume", "llm"],
        ["experiences", "resume", "llm"],
        ["education", "resume", "llm"],
        ["certifications", "resume", "llm"]
      ]
    }}

    Resume Text:
    {text}
    """

    # 3. Call the Gemini Model
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0, 
                response_mime_type="application/json", # Forces strict JSON output
            )
        )
        
        # 4. Parse JSON and apply the anti-hallucination check
        parsed_data = json.loads(response.text)

        print("\n=== RAW LLM JSON OUTPUT ===")
        print(json.dumps(parsed_data, indent=4))
        print("===========================\n")

        verified_data = verify_no_hallucinations(parsed_data, text)
        return verified_data

    except Exception as e:
        print(f"Error during Gemini parsing: {e}")
        return {} # Return empty dict on failure to not crash the Streamlit pipeline

def parse_ats_json(file_bytes: bytes) -> dict:
    """Parses raw ATS JSON blobs."""
    try:
        data = json.loads(file_bytes.decode('utf-8'))
        return data
    except json.JSONDecodeError:
        return {}