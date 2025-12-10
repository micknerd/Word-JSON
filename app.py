import streamlit as st
import os
import tempfile
import json
from parser import parse_document
from translator import translate_segments
from reconstructor import reconstruct_docx

st.set_page_config(page_title="IFRS Translation AI", layout="centered")

st.title("📄 IFRS Document Translator")
st.markdown("Upload a Word document (.docx) to translate it using AWS Bedrock (Claude).")

# Sidebar for optional settings (in future)
with st.sidebar:
    st.header("Settings")
    st.info("Ensure AWS Credentials are set in App Runner configuration.")

uploaded_file = st.file_uploader("Choose a .docx file", type="docx")

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    if st.button("Start Translation"):
        with st.spinner("Processing... Please wait."):
            try:
                tmp_paths = []
                # Create temp files for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    input_path = tmp_input.name
                    tmp_paths.append(input_path)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_json:
                    json_path = tmp_json.name
                    tmp_paths.append(json_path)
                    
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_output:
                    output_path = tmp_output.name
                    tmp_paths.append(output_path)

                # 1. Parse
                status_text = st.empty()
                status_text.text("Parsing document...")
                parsed_data = parse_document(input_path)
                
                # 2. Translate
                status_text.text("Translating with Claude 3 (this may take a minute)...")
                # TODO: Add glossary support in UI if needed
                translated_data = translate_segments(parsed_data)
                
                if not translated_data:
                    st.error("Translation returned empty result. Check logs/credentials.")
                else:
                    # Save intermediate JSON (optional, for debug or download?)
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(translated_data, f, ensure_ascii=False, indent=2)

                    # 3. Reconstruct
                    status_text.text("Reconstructing document...")
                    reconstruct_docx(input_path, json_path, output_path)
                    
                    status_text.text("Done!")
                    st.success("Translation Complete!")
                    
                    # Read result for download
                    with open(output_path, "rb") as f:
                        btn = st.download_button(
                            label="Download Translated Document",
                            data=f,
                            file_name=f"translated_{uploaded_file.name}",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                
                # Cleanup manually? tempfile with delete=False needs manual cleanup.
                # OS usually handles /tmp cleanup eventually, but good practice.
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                # Cleanup temp files
                if 'tmp_paths' in locals():
                    for p in tmp_paths:
                        try:
                            os.remove(p)
                        except Exception:
                            # Best-effort cleanup
                            continue
