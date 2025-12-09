import streamlit as st
import os
import shutil
import tempfile
import json
from parser import parse_document
from translator import translate_segments
from reconstructor import reconstruct_docx

st.set_page_config(page_title="IFRS Translation System", layout="wide")

st.title("IFRS Document Translation System (Claude Opus)")
st.markdown("""
This system translates Japanese IFRS documents to English using **Claude 3 Opus**.
It preserves the original Word layout and provides:
- **Red Highlighting**: For uncertain translations.
- **AI Comments**: Explanations for specific translations or alerts.
""")

# File Uploader
uploaded_file = st.file_uploader("Upload a Word Document (.docx)", type="docx")

if uploaded_file is not None:
    st.info("File uploaded successfully. Processing...")
    
    # Create temp dir for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.docx")
        json_path = os.path.join(temp_dir, "translation.json")
        output_path = os.path.join(temp_dir, "output.docx")
        
        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Step 1: Parse
        with st.status("Step 1: Parsing Document...", expanded=True) as status:
            try:
                parsed_data = parse_document(input_path)
                st.write(f"Parsed {len(parsed_data.get('segments', []))} segments.")
                status.update(label="Parsing Complete", state="complete")
            except Exception as e:
                st.error(f"Parsing failed: {e}")
                st.stop()
        
        # Step 2: Translate
        with st.status("Step 2: Translating with Claude 3 Opus...", expanded=True) as status:
            try:
                # Load context/glossary if available (future feature)
                translations = translate_segments(parsed_data)
                
                if not translations:
                    st.error("Translation returned empty result.")
                    st.stop()
                
                # Save intermediate JSON
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(translations, f, indent=2, ensure_ascii=False)
                    
                st.write("Translation complete.")
                status.update(label="Translation Complete", state="complete")
            except Exception as e:
                st.error(f"Translation failed: {e}")
                st.stop()
                
        # Step 3: Reconstruct
        with st.status("Step 3: Reconstructing Word Document...", expanded=True) as status:
            try:
                reconstruct_docx(input_path, json_path, output_path)
                st.write("Document reconstructed with highlighting and comments.")
                status.update(label="Reconstruction Complete", state="complete")
            except Exception as e:
                st.error(f"Reconstruction failed: {e}")
                st.stop()
                
        # Download Button
        with open(output_path, "rb") as f:
            st.download_button(
                label="Download Translated Document",
                data=f,
                file_name=f"translated_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        # Debug: Show JSON
        with st.expander("View Intermediate JSON"):
            st.json(translations)
