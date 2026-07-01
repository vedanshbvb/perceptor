from typing import Dict, List, Tuple, Set

class ProfileMerger:
    
    def _jaccard_confidence(self, set_a: Set[str], set_b: Set[str]) -> float:
        """Calculates Intersection / Union and scales to a 0-10 confidence score."""
        if not set_a and not set_b:
            return 10.0 # Both empty means they match perfectly
        
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        
        return (intersection / union) * 10.0

    def merge_profiles(self, resume_data: dict, ats_data: dict) -> dict:
        """Merges resume and ats dictionaries belonging to the same phone number."""
        
        # Base case: if one is missing, return the other with confidence 9
        if not resume_data and ats_data:
            ats_data['overall_confidence'] = 9.0
            return ats_data
        if not ats_data and resume_data:
            resume_data['overall_confidence'] = 9.0
            return resume_data
            
        merged = {}
        confidences = {}

        # 1. Full Name
        name_r = resume_data.get("full_name", "")
        name_a = ats_data.get("full_name", "")
        if name_r == name_a:
            merged["full_name"] = name_r
            confidences["name"] = 10.0
        else:
            merged["full_name"] = name_r if len(name_r) >= len(name_a) else name_a
            confidences["name"] = 9.0

        # 2. Emails
        emails_r = set(resume_data.get("emails", []))
        emails_a = set(ats_data.get("emails", []))
        if emails_r == emails_a:
            confidences["emails"] = 10.0
        else:
            confidences["emails"] = 9.0
        merged["emails"] = list(emails_r.union(emails_a))

        # 3. Location (Not included in final conf average per your rules)
        loc_r = resume_data.get("curr_location", [])
        loc_a = ats_data.get("curr_location", [])
        if loc_r == loc_a:
            merged["curr_location"] = loc_r
        else:
            merged["curr_location"] = loc_r if loc_r else loc_a

        # 4. Links
        def flatten_links(link_list):
            flat_set = set()
            for item in link_list:
                if isinstance(item, list):
                    # If it's the nested "other links" list, add its contents
                    flat_set.update(item)
                elif isinstance(item, str) and item.strip():
                    # If it's a normal string link, add it directly
                    flat_set.add(item.strip())
            return flat_set

        links_r = flatten_links(resume_data.get("links", []))
        links_a = flatten_links(ats_data.get("links", []))
        
        if links_r == links_a:
            confidences["links"] = 10.0
        else:
            confidences["links"] = 9.0
            
        merged["links"] = list(links_r.union(links_a))

        # 5. Skills
        # format: (skillname, rating, [sources])
        skills_r = resume_data.get("skills", [])
        skills_a = ats_data.get("skills", [])
        
        if skills_r == skills_a:
            confidences["skills"] = 10.0
            merged["skills"] = skills_r
        else:
            skill_dict = {}
            for s in skills_r + skills_a:
                if len(s) == 3:
                    name, rating, sources = s
                    key = name.lower().strip()
                    if key not in skill_dict:
                        skill_dict[key] = []
                    skill_dict[key].append(s)
            
            merged_skills = []
            for key, items in skill_dict.items():
                true_name = items[0][0] 
                avg_rating = sum(item[1] for item in items) / len(items)
                merged_srcs = list(set(src for item in items for src in item[2]))
                merged_skills.append((true_name, avg_rating, merged_srcs))
            
            merged["skills"] = merged_skills
            
            # Confidence logic: A intersection B / A union B
            names_r = set(s[0].lower().strip() for s in skills_r if len(s) == 3)
            names_a = set(s[0].lower().strip() for s in skills_a if len(s) == 3)
            confidences["skills"] = self._jaccard_confidence(names_r, names_a)

        # 6. Experience
        # format: (company, title, start, end, summary)
        exp_r = resume_data.get("experiences", [])
        exp_a = ats_data.get("experiences", [])
        
        if exp_r == exp_a:
            confidences["experience"] = 10.0
            merged["experiences"] = exp_r
        else:
            exp_dict = {}
            for e in exp_r + exp_a:
                if len(e) == 5:
                    c, t, s, end, summ = e
                    key = c.lower().strip()
                    if key not in exp_dict:
                        exp_dict[key] = []
                    exp_dict[key].append(e)

            merged_exps = []
            for key, items in exp_dict.items():
                true_comp = items[0][0]
                best_title = max([item[1] for item in items], key=len)
                best_summ = max([item[4] for item in items], key=len)
                
                starts = set(item[2] for item in items if item[2])
                ends = set(item[3] for item in items if item[3])
                final_start = starts.pop() if len(starts) == 1 else ""
                final_end = ends.pop() if len(ends) == 1 else ""
                
                merged_exps.append((true_comp, best_title, final_start, final_end, best_summ))
                
            merged["experiences"] = merged_exps
            
            comp_r = set(e[0].lower().strip() for e in exp_r if len(e) == 5)
            comp_a = set(e[0].lower().strip() for e in exp_a if len(e) == 5)
            confidences["experience"] = self._jaccard_confidence(comp_r, comp_a)

        # 7. Education
        # format: (institute, degree, field, end_year)
        edu_r = resume_data.get("education", [])
        edu_a = ats_data.get("education", [])
        
        if edu_r == edu_a:
            confidences["education"] = 10.0
            merged["education"] = edu_r
        else:
            edu_dict = {}
            for e in edu_r + edu_a:
                if len(e) == 4:
                    inst, deg, fld, yr = e
                    key = inst.lower().strip()
                    if key not in edu_dict:
                        edu_dict[key] = []
                    edu_dict[key].append(e)
                    
            merged_edu = []
            for key, items in edu_dict.items():
                true_inst = items[0][0]
                best_deg = max([item[1] for item in items], key=len)
                
                # Choose the pair (field, end_year) with the highest end_year
                best_pair = max(items, key=lambda x: int(x[3]) if x[3] else 0)
                best_fld = best_pair[2]
                best_yr = best_pair[3]
                
                merged_edu.append((true_inst, best_deg, best_fld, best_yr))
                
            merged["education"] = merged_edu
            
            inst_r = set(e[0].lower().strip() for e in edu_r if len(e) == 4)
            inst_a = set(e[0].lower().strip() for e in edu_a if len(e) == 4)
            confidences["education"] = self._jaccard_confidence(inst_r, inst_a)

        # Retain untouched fields
        merged["phone"] = resume_data.get("phone") or ats_data.get("phone")
        merged["yoe"] = max(resume_data.get("yoe", 0), ats_data.get("yoe", 0))
        merged["certifications"] = list(set(resume_data.get("certifications", [])).union(ats_data.get("certifications", [])))
        merged["provenance"] = resume_data.get("provenance", []) + ats_data.get("provenance", [])

        # Final Confidence Math
        total_conf = (
            confidences["name"] + 
            confidences["emails"] + 
            confidences["links"] + 
            confidences["skills"] + 
            confidences["experience"] + 
            confidences["education"]
        )
        merged["overall_confidence"] = round(total_conf / 6.0, 2)

        return merged