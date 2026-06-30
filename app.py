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

    # Process Resumes
    if resume_files:
        st.subheader("Parsed Resumes")
        for pdf in resume_files:
            raw_pdf_dict = parse_resume_pdf(pdf.read())
            field_normalized = field_norm.normalize(raw_pdf_dict, source_type="resume")
            final_data = data_norm.apply_data_normalization(field_normalized, source_type="resume")
            results.append(final_data)
            st.json(final_data)

    # Process ATS JSONs
    if ats_files:
        st.subheader("Parsed ATS Blobs")
        for json_file in ats_files:
            raw_json_dict = parse_ats_json(json_file.read())
            field_normalized = field_norm.normalize(raw_json_dict, source_type="ats")
            final_data = data_norm.apply_data_normalization(field_normalized, source_type="ats")
            results.append(final_data)
            st.json(final_data)

    if not resume_files and not ats_files:
        st.warning("Please upload files first.")