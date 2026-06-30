import re
from models import NormalizedCandidate

class FieldNormalizer:
    def __init__(self):
        # Maps for different incoming schemas
        self.resume_key_map = {
            "candidate_name": "full_name",
            "contact_emails": "emails",
            "phone_num": "phone"
        }
        self.ats_key_map = {
            "name": "full_name",
            "email_addresses": "emails",
            "telephone": "phone",
            "years_of_exp": "yoe"
        }

    def normalize(self, raw_data: dict, source_type: str) -> dict:
        """Normalizes keys from raw dictionaries to the standard schema."""
        mapping = self.resume_key_map if source_type == "resume" else self.ats_key_map
        normalized_data = {}
        
        for raw_key, value in raw_data.items():
            std_key = mapping.get(raw_key, raw_key)
            normalized_data[std_key] = value
            
        return normalized_data

class DataNormalizer:
    def __init__(self):
        # Aliases for fuzzy/imperfect matching
        self.title_aliases = {
            "Software Development Engineer 1": ["sde1", "sde 1", "softwre dev eng", "software developer 1"]
        }
        self.company_aliases = {
            "Life Insurance Corporation": ["lic", "life insurance corporation", "life insurance corp"]
        }
        self.institution_aliases = {
            "Indian Institute of Technology Bombay": ["iitb", "iit bombay"],
            "Indian Institute of Technology Bhilai": ["iitbhilai", "iit bhilai"]
        }
        self.degree_aliases = {
            "Master of Technology": ["mtech", "m.tech", "mtch", "masters in technology"],
            "Bachelor of Technology": ["btech", "b.tech", "bachelors of technology"]
        }
        self.field_aliases = {
            "Mechanical Engineering": ["me", "mech eng"],
            "Electrical Engineering": ["ee", "electrical eng"]
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