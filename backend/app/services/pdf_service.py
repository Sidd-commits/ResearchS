"""
PDF Ingestion, Text Extraction, Cleaning, and Chunking Service for ResearchS.

Handles:
1. Extraction: High-performance extraction via PyMuPDF with pypdf fallback.
2. Cleaning: Removal of academic noise, citation tags, broken line-break hyphens,
   arXiv header banners, and whitespace normalization.
3. Chunking: Recursive, sentence-aware sliding window chunking with configurable
   overlap tailored for Transformer models (FLAN-T5, BART, LongT5).
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("researchs.pdf_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class PDFPreprocessingError(Exception):
    """Custom exception raised when PDF extraction or preprocessing fails."""
    pass


class PDFService:
    """Service class for PDF text extraction, academic cleaning, and chunking."""

    def __init__(
        self,
        default_chunk_chars: int = 1200,
        default_overlap_chars: int = 200,
    ) -> None:
        self.default_chunk_chars = default_chunk_chars
        self.default_overlap_chars = default_overlap_chars

    # =========================================================================
    # STEP 17: PDF TEXT EXTRACTION
    # =========================================================================

    def extract_text(self, pdf_path: str | Path) -> Dict[str, Any]:
        """
        Extract raw text and page-level metadata from a PDF file.
        Uses PyMuPDF as the primary engine, falling back to PyPDF if needed.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise PDFPreprocessingError(f"PDF file not found at: {path}")

        try:
            return self._extract_with_pymupdf(path)
        except Exception as pymupdf_err:
            logger.warning(
                f"PyMuPDF extraction failed for {path.name}: {pymupdf_err}. "
                "Attempting fallback to PyPDF..."
            )
            try:
                return self._extract_with_pypdf(path)
            except Exception as pypdf_err:
                raise PDFPreprocessingError(
                    f"Failed to extract text using both PyMuPDF ({pymupdf_err}) "
                    f"and PyPDF ({pypdf_err})"
                )

    def _extract_with_pymupdf(self, path: Path) -> Dict[str, Any]:
        import pymupdf  # type: ignore

        doc = pymupdf.open(str(path))
        page_records: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text("text") or ""
                text_stripped = text.strip()

                page_records.append({
                    "page_number": page_index + 1,
                    "char_count": len(text_stripped),
                    "word_count": len(text_stripped.split()),
                    "text": text_stripped,
                })
                if text_stripped:
                    full_text_parts.append(text_stripped)

            raw_text = "\n\n".join(full_text_parts)
            return {
                "extractor": "PyMuPDF",
                "page_count": len(doc),
                "raw_text": raw_text,
                "raw_char_count": len(raw_text),
                "raw_word_count": len(raw_text.split()),
                "pages": page_records,
            }
        finally:
            doc.close()

    def _extract_with_pypdf(self, path: Path) -> Dict[str, Any]:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(path))
        page_records: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for page_index, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text_stripped = text.strip()

            page_records.append({
                "page_number": page_index + 1,
                "char_count": len(text_stripped),
                "word_count": len(text_stripped.split()),
                "text": text_stripped,
            })
            if text_stripped:
                full_text_parts.append(text_stripped)

        raw_text = "\n\n".join(full_text_parts)
        return {
            "extractor": "PyPDF",
            "page_count": len(reader.pages),
            "raw_text": raw_text,
            "raw_char_count": len(raw_text),
            "raw_word_count": len(raw_text.split()),
            "pages": page_records,
        }

    # =========================================================================
    # STEP 18 (Part A): TEXT CLEANING & NORMALIZATION
    # =========================================================================

    def clean_text(
        self,
        text: str,
        strip_citations: bool = True,
        remove_arxiv_headers: bool = True,
    ) -> str:
        """
        Cleans raw research paper text for NLP model consumption.

        Pipeline:
        1. Fix words hyphenated across line-breaks (e.g. 'trans-\\nformer' -> 'transformer').
        2. Remove arXiv stamp headers (e.g. 'arXiv:2301.12345v1 [cs.CL] 15 Jan 2023').
        3. Remove standalone page numbers or headers/footers.
        4. Normalize or remove academic citation brackets (e.g. '[1]', '[2, 3]', '[4-7]').
        5. Normalize repeated whitespaces, tabs, and paragraph line breaks.
        """
        if not text:
            return ""

        cleaned = text

        # 1. Rejoin hyphenated words broken across line breaks (e.g. "atten-\ntion" -> "attention")
        cleaned = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", cleaned)

        # 2. Remove arXiv header banners and pre-print stamps
        if remove_arxiv_headers:
            cleaned = re.sub(
                r"arXiv:\d{4}\.\d{4,5}(v\d+)?\s*\[[a-zA-Z\-.]+\]\s*\d{1,2}\s+[a-zA-Z]+\s+\d{4}",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

        # 3. Remove standalone page numbers on isolated lines (e.g. "\n 14 \n")
        cleaned = re.sub(r"(?m)^\s*(page\s+)?\d+\s*(of\s+\d+)?\s*$", "", cleaned, flags=re.IGNORECASE)

        # 4. Remove standard academic citation brackets like [1], [1, 2], [1-4]
        if strip_citations:
            cleaned = re.sub(r"\[\s*\d+(?:[\s,\-–]+\d+)*\s*\]", "", cleaned)

        # 5. Clean URLs or DOIs if they appear isolated
        cleaned = re.sub(r"(https?://[^\s]+|doi:\s*[^\s]+)", "", cleaned)

        # 6. Normalize non-breaking spaces and irregular unicode whitespaces
        cleaned = cleaned.replace("\xa0", " ").replace("\u200b", "")

        # 7. Normalize multiple spaces on the same line into a single space
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 8. Normalize multiple newlines: collapse 3+ newlines into 2 (paragraph break)
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)

        # 9. Trim outer whitespace
        return cleaned.strip()

    # =========================================================================
    # STEP 18 (Part B): SENTENCE-AWARE SLIDING WINDOW CHUNKING
    # =========================================================================

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Splits cleaned text into overlapping chunks respecting sentence boundaries.

        Why sentence-aware chunking matters for Transformers:
        - Avoids truncating words or cutting sentences mid-clause.
        - The overlap preserves narrative flow across chunk boundaries so
          summarizers and Q&A models do not lose context.
        """
        target_size = chunk_size or self.default_chunk_chars
        overlap = chunk_overlap or self.default_overlap_chars

        if not text:
            return []

        # Split text into sentences using sentence boundary regex
        # Recognizes period, exclamation, or question mark followed by space or newline
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        chunks: List[Dict[str, Any]] = []
        current_chunk_sentences: List[str] = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # If adding this sentence exceeds target size and current chunk is not empty
            if current_length + sentence_len > target_size and current_chunk_sentences:
                chunk_body = " ".join(current_chunk_sentences).strip()
                chunks.append(self._format_chunk(chunk_index, chunk_body))
                chunk_index += 1

                # Calculate overlap: retain the last sentences that fit within 'overlap' characters
                overlap_sentences: List[str] = []
                overlap_len = 0
                for rev_s in reversed(current_chunk_sentences):
                    if overlap_len + len(rev_s) <= overlap:
                        overlap_sentences.insert(0, rev_s)
                        overlap_len += len(rev_s) + 1
                    else:
                        break

                current_chunk_sentences = overlap_sentences
                current_length = sum(len(s) + 1 for s in current_chunk_sentences)

            current_chunk_sentences.append(sentence)
            current_length += sentence_len + 1

        # Add any remaining sentences as the final chunk
        if current_chunk_sentences:
            chunk_body = " ".join(current_chunk_sentences).strip()
            chunks.append(self._format_chunk(chunk_index, chunk_body))

        return chunks

    def _format_chunk(self, index: int, text: str) -> Dict[str, Any]:
        words = text.split()
        # Rough token estimate: ~1 token per 4 chars or ~1.3 tokens per word in English
        est_tokens = max(1, round(len(text) / 4))
        return {
            "chunk_index": index,
            "text": text,
            "char_count": len(text),
            "word_count": len(words),
            "estimated_tokens": est_tokens,
        }

    # =========================================================================
    # COMPLETE PREPROCESSING PIPELINE
    # =========================================================================

    def process_pdf(
        self,
        pdf_path: str | Path,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes the full pipeline:
        1. Extract text from PDF
        2. Clean research paper noise and formatting
        3. Chunk cleaned text into sentence-aware blocks
        4. Return aggregated statistics and metadata
        """
        path = Path(pdf_path)
        extracted = self.extract_text(path)
        raw_text = extracted["raw_text"]

        cleaned_text = self.clean_text(raw_text)
        chunks = self.chunk_text(
            cleaned_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        cleaned_word_count = len(cleaned_text.split())
        cleaned_char_count = len(cleaned_text)

        preview_length = min(800, len(cleaned_text))
        preview = cleaned_text[:preview_length] + ("..." if len(cleaned_text) > preview_length else "")

        return {
            "status": "success",
            "filename": path.name,
            "extractor": extracted["extractor"],
            "page_count": extracted["page_count"],
            "raw_metrics": {
                "character_count": extracted["raw_char_count"],
                "word_count": extracted["raw_word_count"],
            },
            "cleaned_metrics": {
                "character_count": cleaned_char_count,
                "word_count": cleaned_word_count,
                "noise_reduction_pct": round(
                    ((extracted["raw_char_count"] - cleaned_char_count) / max(1, extracted["raw_char_count"])) * 100,
                    2,
                ),
            },
            "chunking": {
                "total_chunks": len(chunks),
                "target_chunk_chars": chunk_size or self.default_chunk_chars,
                "overlap_chars": chunk_overlap or self.default_overlap_chars,
            },
            "preview_text": preview,
            "chunks": chunks,
        }


# Singleton instance for easy import across the application
pdf_service = PDFService()
