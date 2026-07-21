"""
Business Analyst Service.

WHY: This is the single orchestration point for the whole Phase 1 workflow:
    upload -> detect type -> extract -> clean -> agent -> version 1
    refine  -> agent -> version N
    mark final

The UI layer (Streamlit) should never call parsers, the agent, or the
version service directly — it only ever talks to this service. That keeps
the UI "dumb" (just rendering) and the business logic reusable if the UI is
later swapped for a real web frontend.
"""

from pathlib import Path

from app.agents.business_analyst.agent import BusinessAnalystAgent, ProjectMetadata
from app.parsers.detector import DocumentType, detect_document_type
from app.parsers.docx_parser import extract_text_from_docx
from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.text_cleaner import clean_text
from app.parsers.text_parser import extract_text_from_txt
from app.services.version_service import BRDVersion, VersionService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UnsupportedFileTypeError(Exception):
    pass


class EmptyDocumentError(Exception):
    pass


class BusinessAnalystService:
    """Orchestrates the full SOW -> BRD workflow for a single project."""

    def __init__(self, project_id: str, agent: BusinessAnalystAgent | None = None):
        self.project_id = project_id
        self._agent = agent or BusinessAnalystAgent()
        self._version_service = VersionService(project_id=project_id)

    # --- step 1: extraction ---------------------------------------------------

    def extract_text(self, file_path: str | Path) -> str:
        """Detect file type and extract raw text. Raises for unsupported/empty files."""
        doc_type = detect_document_type(file_path)
        logger.info(f"Detected document type '{doc_type.value}' for '{file_path}'")

        if doc_type == DocumentType.DOCX:
            raw_text = extract_text_from_docx(file_path)
        elif doc_type == DocumentType.PDF:
            raw_text = extract_text_from_pdf(file_path)
        elif doc_type == DocumentType.TXT:
            raw_text = extract_text_from_txt(file_path)
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported file type for '{file_path}'. Supported: .docx, .pdf, .txt"
            )

        if not raw_text or not raw_text.strip():
            raise EmptyDocumentError(f"No extractable text found in '{file_path}'")

        return raw_text

    # --- step 2: cleaning -------------------------------------------------------

    def preprocess(self, raw_text: str) -> str:
        return clean_text(raw_text)

    # --- step 3: generate BRD v1 -------------------------------------------------

    def generate_initial_brd(self, file_path: str | Path, metadata: ProjectMetadata) -> BRDVersion:
        """Full pipeline: extract -> clean -> generate -> store as version 1."""
        raw_text = self.extract_text(file_path)
        clean_sow = self.preprocess(raw_text)
        brd_text = self._agent.generate_brd(clean_sow, metadata)
        return self._version_service.add_version(
            content=brd_text, source="initial", note="Generated from SOW"
        )

    # --- step 4a: manual edit -----------------------------------------------------

    def save_manual_edit(self, edited_content: str, note: str = "Manual edit") -> BRDVersion:
        if not edited_content or not edited_content.strip():
            raise ValueError("Cannot save an empty BRD")
        return self._version_service.add_version(
            content=edited_content, source="manual_edit", note=note
        )

    # --- step 4b: AI refine ---------------------------------------------------------

    def refine_with_ai(self, user_feedback: str) -> BRDVersion:
        latest = self._version_service.get_latest_version()
        if latest is None:
            raise ValueError("No existing BRD version to refine. Generate an initial BRD first.")

        refined_text = self._agent.refine_brd(
            current_brd=latest.content,
            user_feedback=user_feedback,
            current_version=latest.version,
        )
        return self._version_service.add_version(
            content=refined_text, source="ai_refine", note=user_feedback
        )

    # --- version history / finalization ------------------------------------------------

    def get_all_versions(self) -> list[BRDVersion]:
        return self._version_service.get_all_versions()

    def get_version(self, version_number: int) -> BRDVersion | None:
        return self._version_service.get_version(version_number)

    def choose_final_brd(self, version_number: int) -> BRDVersion:
        return self._version_service.mark_final(version_number)

    def get_final_brd(self) -> BRDVersion | None:
        return self._version_service.get_final_version()
