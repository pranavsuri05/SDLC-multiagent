"""
Streamlit UI for Phase 1: SOW -> BRD Business Analyst Agent.

WHY STREAMLIT FOR PHASE 1: The spec's UI requirements (upload, view, edit,
refine, version history, final selection, download) map directly onto
Streamlit widgets, and it lets a single Python process serve as both backend
and frontend — no separate API server or JS build step needed yet. Business
logic still lives entirely in app/agents and app/services; this file ONLY
renders widgets and calls that layer, so a real web frontend can replace it
later without touching business logic.

Run with:  streamlit run app/ui/streamlit_app.py
"""
import os
import sys
import time
import uuid
from pathlib import Path

import streamlit as st

# Only load st.secrets if a secrets.toml actually exists (Streamlit Cloud).
# Locally we rely on .env instead — touching st.secrets when no file exists
# triggers Streamlit's own "No secrets found" warning as a side effect, which
# then breaks the set_page_config()-must-be-first rule further down.
_project_root = Path(__file__).resolve().parents[2]
_secrets_candidates = [
    _project_root / ".streamlit" / "secrets.toml",
    Path.home() / ".streamlit" / "secrets.toml",
]
if any(p.exists() for p in _secrets_candidates):
    try:
        for _key, _value in st.secrets.items():
            os.environ.setdefault(_key, str(_value))
    except Exception:
        pass

sys.path.append(str(_project_root))

from app.agents.business_analyst.agent import BusinessAnalystAgentError, ProjectMetadata
from app.agents.business_analyst.service import (
    BusinessAnalystService,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)
from app.document_generator.brd_generator import generate_brd_docx
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="BA Agent — SOW to BRD", layout="wide")


# --- session bootstrapping ---------------------------------------------------------------

if "project_id" not in st.session_state:
    st.session_state.project_id = str(uuid.uuid4())[:8]

if "service" not in st.session_state:
    st.session_state.service = BusinessAnalystService(project_id=st.session_state.project_id)

service: BusinessAnalystService = st.session_state.service


def refresh_versions():
    st.session_state.versions = service.get_all_versions()


if "versions" not in st.session_state:
    refresh_versions()


# --- sidebar: version history --------------------------------------------------------------

with st.sidebar:
    st.header("Version History")
    st.caption(f"Project ID: `{st.session_state.project_id}`")

    if not st.session_state.versions:
        st.info("No versions yet. Generate a BRD to get started.")
    else:
        for v in reversed(st.session_state.versions):
            label = f"v{v.version} — {v.source}"
            if v.is_final:
                label += " -- FINAL Doc "
            with st.expander(label):
                st.caption(f"Created: {v.created_at}")
                if v.note:
                    st.caption(f"Note: {v.note}")
                if st.button("View this version", key=f"view_{v.version}"):
                    st.session_state.viewing_version = v.version
                if not v.is_final:
                    if st.button("Choose as Final BRD", key=f"final_{v.version}"):
                        service.choose_final_brd(v.version)
                        refresh_versions()
                        st.success(f"Version {v.version} marked as Final BRD.")
                        st.rerun()

    st.divider()
    if st.button("🔄 Start New Project"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# --- main area ---------------------------------------------------------------------------------

st.title("Business Analyst Agent — SOW → BRD")
st.caption("Phase 1: Statement of Work → Business Requirement Document")

latest_version = st.session_state.versions[-1] if st.session_state.versions else None
final_version = next((v for v in st.session_state.versions if v.is_final), None)

tab_generate, tab_workspace = st.tabs(["1. Upload & Generate", "2.Review, Edit & Finalize"])


# --- TAB 1: upload + generate --------------------------------------------------------------------

with tab_generate:
    if latest_version is not None:
        st.info("A BRD already exists for this project. Go to the 'Review, Edit & Finalize' tab, "
                "or start a new project from the sidebar to upload a different SOW.")
    else:
        st.subheader("Project Details")
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name", placeholder="e.g. Customer Portal Revamp")
            client_name = st.text_input("Client Name", placeholder="e.g. Acme Corp")
        with col2:
            project_type = st.selectbox(
                "Project Type", ["Web Application", "Mobile Application", "Data Platform",
                                  "API / Integration", "Internal Tool", "Other"]
            )
            industry = st.text_input("Industry", placeholder="e.g. Banking, Retail, Healthcare")

        st.subheader("Upload Statement of Work (SOW)")
        uploaded_file = st.file_uploader("Supported formats: DOCX, PDF, TXT", type=["docx", "pdf", "txt"])

        generate_disabled = not (uploaded_file and project_name and client_name and industry)

        if st.button("Generate BRD", disabled=generate_disabled, type="primary"):
            upload_path = settings.resolved_upload_dir() / f"{st.session_state.project_id}_{uploaded_file.name}"
            upload_path.write_bytes(uploaded_file.getbuffer())

            metadata = ProjectMetadata(
                project_name=project_name,
                client_name=client_name,
                project_type=project_type,
                industry=industry,
            )

            with st.spinner("Extracting document, cleaning text, and generating your BRD with Gemini..."):
                try:
                    start = time.time()
                    version = service.generate_initial_brd(upload_path, metadata)
                    elapsed = time.time() - start
                    logger.info(f"BRD v1 generated in {elapsed:.1f}s")
                    refresh_versions()
                    st.success(f"BRD Version {version.version} generated in {elapsed:.1f}s!")
                    st.rerun()
                except UnsupportedFileTypeError as e:
                    st.error(f"Unsupported file: {e}")
                except EmptyDocumentError as e:
                    st.error(f"Empty document: {e}")
                except BusinessAnalystAgentError as e:
                    st.error(f"AI generation failed: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error generating BRD: {e}")
                    st.error(f"Unexpected error: {e}")


# --- TAB 2: review / edit / refine / finalize / download ------------------------------------------

with tab_workspace:
    if latest_version is None:
        st.info("Upload a SOW and generate a BRD first (see Tab 1).")
    else:
        viewing_number = st.session_state.get("viewing_version", latest_version.version)
        viewing_version = service.get_version(viewing_number) or latest_version

        st.subheader(f"Viewing Version {viewing_version.version}"
                      + (" (|Final BRD|)" if viewing_version.is_final else ""))

        is_locked = final_version is not None and viewing_version.version == final_version.version

        edited_text = st.text_area(
            "BRD Content (editable like a document)",
            value=viewing_version.content,
            height=500,
            disabled=is_locked,
            key=f"editor_{viewing_version.version}",
        )

        col_a, col_b, col_c = st.columns([1, 1, 2])

        with col_a:
            if st.button("Save Manual Edit", disabled=is_locked):
                try:
                    new_version = service.save_manual_edit(edited_text)
                    refresh_versions()
                    st.session_state.viewing_version = new_version.version
                    st.success(f"Saved as Version {new_version.version}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        with col_b:
            if not viewing_version.is_final:
                if st.button("Choose as Final BRD"):
                    service.choose_final_brd(viewing_version.version)
                    refresh_versions()
                    st.success(f"Version {viewing_version.version} is now the Final BRD.")
                    st.rerun()

        with col_c:
            docx_path = Path(settings.resolved_output_dir()) / st.session_state.project_id / f"BRD_v{viewing_version.version}.docx"
            if st.button("Prepare .docx for download"):
                with st.spinner("Formatting Word document..."):
                    generate_brd_docx(viewing_version.content, docx_path)
                st.session_state.docx_ready_path = str(docx_path)

            if st.session_state.get("docx_ready_path") and Path(st.session_state.docx_ready_path).exists():
                with open(st.session_state.docx_ready_path, "rb") as f:
                    st.download_button(
                        "⬇Download BRD.docx",
                        data=f.read(),
                        file_name=f"BRD_v{viewing_version.version}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )

        st.divider()
        st.subheader("Refine with AI")
        st.caption("Describe changes in plain English. Only affected sections will change — "
                    "everything else is preserved.")
        feedback = st.text_area(
            "e.g. 'Add Multi-Factor Authentication as a functional requirement' or "
            "'Replace MySQL with PostgreSQL everywhere'",
            key="feedback_input",
            disabled=is_locked,
        )
        if st.button("Refine with AI", disabled=is_locked or not feedback.strip()):
            with st.spinner("Sending current BRD + your feedback to Gemini..."):
                try:
                    new_version = service.refine_with_ai(feedback)
                    refresh_versions()
                    st.session_state.viewing_version = new_version.version
                    st.success(f"Created Version {new_version.version} from your feedback.")
                    st.rerun()
                except BusinessAnalystAgentError as e:
                    st.error(f"AI refinement failed: {e}")
                except ValueError as e:
                    st.error(str(e))

        if is_locked:
            st.warning("This version is the Final BRD and is locked. "
                       "To make further changes, view an earlier version and edit that instead — "
                       "it will create a new version without affecting the Final BRD.")
