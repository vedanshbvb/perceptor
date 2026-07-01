# app.py
import streamlit as st
import json
from parsers import parse_resume_pdf, parse_ats_json
from normalizers import FieldNormalizer, DataNormalizer
from merger import ProfileMerger
from projector import apply_projection


# Initialize pipeline components
field_norm = FieldNormalizer()
data_norm = DataNormalizer()
merger = ProfileMerger()

st.title("Candidate Data Normalization Pipeline")

# --- NEW: Config UI ---
st.sidebar.header("Runtime Configuration")
st.sidebar.markdown("Define how to reshape the output.")
default_config = """{
  "fields": [
    {"path": "full_name"},
    {"path": "primary_email", "from": "emails[0]"},
    {"path": "phone"},
    {"path": "skills"},
    {"path": "overall_confidence"}
  ],
  "on_missing": "null"
}"""
config_input = st.sidebar.text_area("JSON Config", value=default_config, height=250)

# Parse the config safely
user_config = None
try:
    if config_input.strip():
        user_config = json.loads(config_input)
except json.JSONDecodeError:
    st.sidebar.error("Invalid JSON format. The pipeline will output the default schema.")

# --- File Uploaders ---
col1, col2 = st.columns(2)
with col1:
    resume_files = st.file_uploader("Input Resume PDFs", type=['pdf'], accept_multiple_files=True)
with col2:
    ats_files = st.file_uploader("Input ATS Json Blobs", type=['json'], accept_multiple_files=True)

if st.button("Process Documents"):
    with st.spinner("Processing documents, please wait..."):
        resume_records = {}
        ats_records = {}

        # Process Resumes
        if resume_files:
            for pdf in resume_files:
                raw_pdf_dict = parse_resume_pdf(pdf.read())
                field_normalized = field_norm.normalize(raw_pdf_dict, source_type="resume")
                final_data = data_norm.apply_data_normalization(field_normalized, source_type="resume")
                
                phone = final_data.get("phone")
                if phone:
                    resume_records[phone] = final_data

        # Process ATS JSONs
        if ats_files:
            for json_file in ats_files:
                raw_json_dict = parse_ats_json(json_file.read())
                field_normalized = field_norm.normalize(raw_json_dict, source_type="ats")
                final_data = data_norm.apply_data_normalization(field_normalized, source_type="ats")
                
                phone = final_data.get("phone")
                if phone:
                    ats_records[phone] = final_data

        # Merge & Project Layer
        st.subheader("Final Configured Profiles")
        final_profiles = []
        
        all_phones = set(resume_records.keys()).union(set(ats_records.keys()))
        
        for phone in all_phones:
            res_data = resume_records.get(phone, {})
            ats_data = ats_records.get(phone, {})
            
            # 1. Merge into the canonical internal schema
            merged_profile = merger.merge_profiles(res_data, ats_data)
            
            # 2. NEW: Project into the requested output schema
            projected_profile = apply_projection(merged_profile, user_config) if user_config else merged_profile
            
            final_profiles.append(projected_profile)
            st.json(projected_profile)

        # Save final merged JSON
        if final_profiles:
            with open("outputs/canonical_profiles.json", "w", encoding="utf-8") as f:
                export_data = final_profiles[0] if len(final_profiles) == 1 else final_profiles
                json.dump(export_data, f, indent=4)
            st.success(f"Successfully processed {len(final_profiles)} candidate(s).")

        if not resume_files and not ats_files:
            st.warning("Please upload files first.")