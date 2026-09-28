"""
frontend/app.py

Streamlit UI for LegalEase. Collects document details, calls the FastAPI
backend to generate the text via Gemini, previews it, allows inline
editing, and offers .txt / .docx / .pdf downloads.

Run with:  streamlit run frontend/app.py
"""

import os
import sys

# Make project root importable (config.py, legalEaseAPI/utils.py) when
# Streamlit is launched with `streamlit run frontend/app.py`.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import streamlit as st

from config import APP_TITLE, APP_ICON, API_BASE_URL, LOGO_PATH
from legalEaseAPI.utils import sanitize_text, format_docx, format_pdf, format_html_preview

st.set_page_config(page_title="LegalEase", page_icon=APP_ICON, layout="centered")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
if os.path.exists(LOGO_PATH):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_PATH, use_container_width=True)
else:
    st.markdown(
        f"<h1 style='text-align:center;'>{APP_ICON} LegalEase</h1>",
        unsafe_allow_html=True,
    )

st.markdown(
    "<h4 style='text-align:center; font-weight:normal; opacity:0.85;'>AI Legal Document Generator</h4>",
    unsafe_allow_html=True,
)
st.divider()

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
st.session_state.setdefault("generated_text", "")
st.session_state.setdefault("show_edit", False)
st.session_state.setdefault("last_doc_type", "")

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------
document_type = st.text_input(
    "Document Type (Ex: Agreement, Contract, NDA)",
    placeholder="e.g. Freelance Work Contract",
)
parties = st.text_area(
    "Parties Involved",
    placeholder="e.g. Jane Doe (Service Provider), TechNova Inc. (Client)",
    height=80,
)
terms = st.text_area(
    "Terms & Conditions (Use semicolons to separate each clause)",
    placeholder="e.g. Payment due within 30 days; Confidentiality maintained at all times",
    height=120,
)
dates = st.text_input("Effective Date", placeholder="e.g. April 15, 2025")

generate_clicked = st.button("Generate Document", type="primary")

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
if generate_clicked:
    if not all([document_type.strip(), parties.strip(), terms.strip(), dates.strip()]):
        st.warning("Please fill in all fields before generating a document.")
    else:
        with st.spinner("Generating your document..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/generate",
                    json={
                        "document_type": document_type,
                        "parties": parties,
                        "terms": terms,
                        "dates": dates,
                    },
                    timeout=60,
                )
                if response.status_code == 200:
                    raw_text = response.json().get("document", "")
                    st.session_state.generated_text = sanitize_text(raw_text)
                    st.session_state.last_doc_type = document_type
                    st.session_state.show_edit = False
                    st.success("Document Generated Successfully!")
                else:
                    detail = response.json().get("detail", response.text)
                    st.error(f"Generation failed ({response.status_code}): {detail}")
            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not reach the backend API. Make sure it's running "
                    f"at {API_BASE_URL} (see the setup instructions)."
                )
            except requests.exceptions.Timeout:
                st.error("The request to the backend timed out. Please try again.")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

# ---------------------------------------------------------------------------
# Preview / Edit / Download
# ---------------------------------------------------------------------------
if not st.session_state.generated_text:
    st.info("Click 'Generate Document' to start.")
else:
    styled_html = format_html_preview(st.session_state.generated_text)
    st.markdown(
        f"""
        <div style='background-color:#0e1117; border:1px solid #333;
                    border-radius:8px; padding:16px 20px; max-height:420px;
                    overflow-y:auto; color:#e6e6e6; line-height:1.5;'>
        {styled_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Click to Edit Document"):
        st.session_state.show_edit = not st.session_state.show_edit

    if st.session_state.show_edit:
        edited_text = st.text_area(
            "Edit Document Below:",
            value=st.session_state.generated_text,
            height=300,
        )
        st.session_state.generated_text = edited_text

    st.divider()
    st.subheader("Download / Save")

    safe_filename = (st.session_state.last_doc_type or "legal_document").strip().replace(" ", "_").lower()
    final_text = st.session_state.generated_text
    doc_type = st.session_state.last_doc_type or document_type

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button(
            "📄 Download as .TXT",
            data=final_text,
            file_name=f"{safe_filename}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl2:
        try:
            docx_bytes = format_docx(final_text, doc_type, parties, terms, dates)
            st.download_button(
                "📝 Download as .DOCX",
                data=docx_bytes,
                file_name=f"{safe_filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Could not build DOCX: {exc}")
    with dl3:
        try:
            pdf_bytes = format_pdf(final_text, doc_type)
            st.download_button(
                "📕 Download as .PDF",
                data=pdf_bytes,
                file_name=f"{safe_filename}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Could not build PDF: {exc}")