import re
from models import NormalizedCandidate

class FieldNormalizer:
    def __init__(self):
        # Target Standard Key -> List of possible incoming raw keys
        self.resume_schema = {
            "full_name": ["candidate_name", "name", "first_last_name"],
            "emails": ["contact_emails", "email", "email_address", "contact_email"],
            "phone": ["phone_num", "mobile", "telephone", "contact_number", "cell"]
        }
        
        self.ats_schema = {
            "full_name": ["name", "candidate_name", "applicant_name", "full_name"],
            "emails": ["email_addresses", "email", "contact_email"],
            "phone": ["mobile", "telephone", "number", "phone_number", "contact_number"],
            "curr_location": ["curr_location"],
            "university": ["college", "university", "institute", "institution", "school"],
            "yoe": ["years_of_exp", "years_of_experience", "total_experience", "experience_years"],
            "experiences": ["professional_experience", "work_experience", "employment_history", "experience"],
            "certifications": ["certificates", "certifications", "licenses"],
            "skills": ["technologies", "languages", "core_competencies", "technical_skills"]
        }

        # Build flat lookup maps once during initialization for O(1) matching
        self._resume_map = self._build_flat_map(self.resume_schema)
        self._ats_map = self._build_flat_map(self.ats_schema)

    def _build_flat_map(self, schema: dict) -> dict:
        """Inverts the schema to raw_key -> standard_key for fast lookups."""
        flat_map = {}
        for std_key, raw_keys in schema.items():
            for raw_key in raw_keys:
                # Ensure all our defined aliases are lowercase and clean
                flat_map[raw_key.lower().strip()] = std_key
        return flat_map

    def normalize(self, raw_data: dict, source_type: str) -> dict:
        """Normalizes keys from raw dictionaries to the standard schema."""
        mapping = self._resume_map if source_type == "resume" else self._ats_map
        normalized_data = {}
        
        for raw_key, value in raw_data.items():
            # 1. Uniformity Check: Lowercase and strip whitespace from incoming key
            cleaned_raw_key = raw_key.lower().strip()
            
            # 2. Match against the map, fallback to the cleaned key if not found
            std_key = mapping.get(cleaned_raw_key, cleaned_raw_key)
            
            normalized_data[std_key] = value
            
        return normalized_data

class DataNormalizer:
    def __init__(self):
        # Extensive aliases for fuzzy/imperfect matching
        self.title_aliases = {
            "Software Development Engineer 1": ["sde1", "sde 1", "softwre dev eng", "software developer 1", "junior software engineer", "swe 1"],
            "Software Development Engineer 2": ["sde2", "sde 2", "software developer 2", "swe 2", "mid level engineer"],
            "Senior Software Engineer": ["sr sde", "senior sde", "sr software engineer", "sse", "senior swe"],
            "Machine Learning Engineer": ["ml engineer", "mle", "machine learning dev", "ai engineer", "ai/ml engineer"],
            "Data Scientist": ["ds", "data analyst", "senior data scientist", "lead data scientist"],
            "Product Manager": ["pm", "product owner", "associate product manager", "apm", "senior product manager"],
            "Frontend Developer": ["ui developer", "front end engineer", "frontend eng", "ui/ux developer", "react developer"],
            "Backend Developer": ["backend engineer", "back end dev", "backend dev", "java developer", "python developer"],
            "Full Stack Developer": ["fullstack developer", "full stack engineer", "fsd", "mern stack developer"],
            "DevOps Engineer": ["devops", "site reliability engineer", "sre", "cloud engineer", "platform engineer"]
        }
        self.company_aliases = {
            "Life Insurance Corporation": ["lic", "life insurance corporation", "life insurance corp"],
            "Google": ["google inc", "google llc", "alphabet"],
            "Amazon": ["amazon web services", "aws", "amazon com"],
            "Microsoft": ["microsoft corp", "microsoft corporation", "msft"],
            "Meta": ["facebook", "fb", "meta platforms", "meta inc"],
            "Apple": ["apple inc", "apple computer"],
            "Netflix": ["netflix inc"],
            "Tata Consultancy Services": ["tcs", "tata consultancy"],
            "Infosys": ["infosys limited", "infosys tech"],
            "Wipro": ["wipro limited", "wipro tech"],
            "Accenture": ["accenture plc", "accenture strategy"]
        }
        self.institution_aliases = {
            "Indian Institute of Technology Bombay": ["iitb", "iit bombay"],
            "Indian Institute of Technology Bhilai": ["iitbhilai", "iit bhilai"],
            "Indian Institute of Technology Delhi": ["iitd", "iit delhi"],
            "Indian Institute of Technology Madras": ["iitm", "iit madras", "iit chennai"],
            "Indian Institute of Technology Kanpur": ["iitk", "iit kanpur"],
            "Indian Institute of Technology Kharagpur": ["iitkgp", "iit khgp", "iit kharagpur"],
            "Birla Institute of Technology and Science, Pilani": ["bits pilani", "bits"],
            "National Institute of Technology Tiruchirappalli": ["nit trichy", "nitt"],
            "Massachusetts Institute of Technology": ["mit"],
            "Stanford University": ["stanford"]
        }
        self.degree_aliases = {
            "Master of Technology": ["mtech", "m.tech", "mtch", "masters in technology"],
            "Bachelor of Technology": ["btech", "b.tech", "bachelors of technology", "b.e.", "bachelor of engineering", "be"],
            "Master of Science": ["msc", "m.s.", "ms", "master of science"],
            "Bachelor of Science": ["bsc", "b.s.", "bs", "bachelor of science"],
            "Doctor of Philosophy": ["phd", "ph.d.", "doctorate", "dphil"],
            "Master of Business Administration": ["mba", "m.b.a.", "pgdm"],
            "Bachelor of Computer Applications": ["bca", "b.c.a."]
        }
        self.field_aliases = {
            "Mechanical Engineering": ["me", "mech eng", "mechanical"],
            "Electrical Engineering": ["ee", "electrical eng", "electrical and electronics engineering", "eee"],
            "Computer Science and Engineering": ["cs", "cse", "computer science", "computer engineering"],
            "Information Technology": ["it", "info tech"],
            "Data Science": ["ds", "data analytics", "data science and artificial intelligence"],
            "Artificial Intelligence": ["ai", "ai/ml", "artificial intelligence and machine learning"],
            "Civil Engineering": ["ce", "civil"],
            "Electronics and Communication Engineering": ["ece", "electronics"]
        }

    def _clean_string(self, text: str) -> str:
        """Removes special characters and spaces for aggressive matching."""
        return re.sub(r'[^a-z0-9]', '', str(text).lower())

    def _match_alias(self, value: str, alias_dict: dict) -> str:
        """Matches a string against the dictionary of aliases."""
        if not value: return value
        cleaned_val = self._clean_string(value)
        
        for target, aliases in alias_dict.items():
            # Check if cleaned target matches
            if cleaned_val == self._clean_string(target):
                return target
            # Check aliases
            for alias in aliases:
                if cleaned_val == self._clean_string(alias):
                    return target
        return value # Return original if no match found

    def apply_data_normalization(self, data: dict, source_type: str) -> NormalizedCandidate:
        """Applies data normalization and enforces the exact target schema."""
        
        # 1. Initialize schema with defaults
        final: NormalizedCandidate = {
            "full_name": str(data.get("full_name", "")),
            "emails": data.get("emails", []),
            "phone": str(data.get("phone", "")),
            "curr_location": data.get("curr_location", []),
            "links": data.get("links", []),
            "yoe": float(data.get("yoe", 0.0)),
            "skills": data.get("skills", []),
            "experiences": [],
            "education": [],
            "certifications": data.get("certifications", []),
            "provenance": [],
            "overall_confidence": 8.5 # Example heuristic
        }

        # 2. Normalize Experiences
        for exp in data.get("experiences", []):
            if len(exp) == 5:
                c, t, s, e, summ = exp
                norm_c = self._match_alias(c, self.company_aliases)
                norm_t = self._match_alias(t, self.title_aliases)
                # Note: Date standardization logic (e.g., handling "MM/YYYY" to "01/MM/YYYY") goes here
                final["experiences"].append((norm_c, norm_t, s, e, summ))

        # 3. Normalize Education
        for edu in data.get("education", []):
            if len(edu) == 4:
                inst, deg, fld, yr = edu
                norm_inst = self._match_alias(inst, self.institution_aliases)
                norm_deg = self._match_alias(deg, self.degree_aliases)
                norm_fld = self._match_alias(fld, self.field_aliases)
                final["education"].append((norm_inst, norm_deg, norm_fld, int(yr)))
        
        # 4. Generate Provenance
        for key in final.keys():
            if key != "provenance":
                final["provenance"].append((key, source_type, ""))

        return final