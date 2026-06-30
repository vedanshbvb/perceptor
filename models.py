from typing import TypedDict, List, Tuple

class NormalizedCandidate(TypedDict):
    full_name: str
    emails: List[str]
    phone: str
    curr_location: List[str]  # [city, region, country]
    links: List[str]          # [leetcode, github, portfolio, other]
    yoe: float
    skills: List[Tuple[str, float, List[str]]]      # (skillname, rating, list of sources)
    experiences: List[Tuple[str, str, str, str, str]] # (company, title, start, end, summary)
    education: List[Tuple[str, str, str, int]]      # (institution, degree, field, end_year)
    certifications: List[str]
    provenance: List[Tuple[str, str, str]]          # (field, source, method)
    overall_confidence: float                       # 0 to 10