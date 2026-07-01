import streamlit as st
import json
from parsers import parse_resume_pdf, parse_ats_json
from normalizers import FieldNormalizer, DataNormalizer

# Initialize pipeline components
field_norm = FieldNormalizer()
data_norm = DataNormalizer()

st.title("Candidate Data Normalization Pipeline")

# Layout for multiple uploads
col1, col2 = st.columns(2)

with col1:
    resume_files = st.file_uploader(
        "Input Resume PDFs", 
        type=['pdf'], 
        accept_multiple_files=True
    )

with col2:
    ats_files = st.file_uploader(
        "Input ATS Json Blobs", 
        type=['json'], 
        accept_multiple_files=True
    )

if st.button("Process Documents"):
    results = []
    
    # Store processed data specifically for exports
    resume_exports = []
    ats_exports = []

    # Process Resumes
    if resume_files:
        st.subheader("Parsed Resumes")
        for pdf in resume_files:
            raw_pdf_dict = parse_resume_pdf(pdf.read())
            field_normalized = field_norm.normalize(raw_pdf_dict, source_type="resume")
            final_data = data_norm.apply_data_normalization(field_normalized, source_type="resume")
            
            resume_exports.append(final_data)
            results.append(final_data)
            st.json(final_data)
            
        # --- NEW: Save to normalised_resume.json ---
        with open("outputs/normalised_resume.json", "w", encoding="utf-8") as f:
            # If only 1 file, save as an object. If multiple, save as a list of objects.
            export_data = resume_exports[0] if len(resume_exports) == 1 else resume_exports
            json.dump(export_data, f, indent=4)
        st.success(f"Saved {len(resume_files)} resume(s) to outputs/normalised_resume.json")

    # Process ATS JSONs
    if ats_files:
        st.subheader("Parsed ATS Blobs")
        for json_file in ats_files:
            raw_json_dict = parse_ats_json(json_file.read())
            field_normalized = field_norm.normalize(raw_json_dict, source_type="ats")
            final_data = data_norm.apply_data_normalization(field_normalized, source_type="ats")
            
            ats_exports.append(final_data)
            results.append(final_data)
            st.json(final_data)
            
        # --- NEW: Save to normalised_ats.json ---
        with open("outputs/normalised_ats.json", "w", encoding="utf-8") as f:
            export_data = ats_exports[0] if len(ats_exports) == 1 else ats_exports
            json.dump(export_data, f, indent=4)
        st.success(f"Saved {len(ats_files)} ATS blob(s) to outputs/normalised_ats.json")

    if not resume_files and not ats_files:
        st.warning("Please upload files first.")