"""
PDF-Based Question Answering and Research Paper Chatbot Service.

Provides context-grounded retrieval-augmented generation (RAG) over
uploaded research paper chunks using TF-IDF ranking and Google FLAN-T5.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.flan_t5 import flan_t5_summarizer
from app.services.pdf_service import pdf_service

logger = logging.getLogger("researchs.services.qa")

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

# Global GPU lock for thread-safe sequential memory management
_QA_LOCK = threading.Lock()


class QAService:
    """Service to answer questions grounded in research paper content."""

    def __init__(self, upload_dir: Path = UPLOAD_DIR) -> None:
        self.upload_dir = upload_dir

    def answer_question(
        self,
        saved_filename: str,
        question: str,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Retrieves relevant paper chunks for the user question and generates
        a context-grounded answer using Google FLAN-T5.
        """
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        file_path = self.upload_dir / saved_filename
        if not file_path.exists():
            raise FileNotFoundError(f"Paper '{saved_filename}' not found.")

        # Process PDF to get structured chunks
        processed = pdf_service.process_pdf(file_path)
        chunks_meta = processed.get("chunks", [])

        if not chunks_meta:
            raw_text = processed.get("preview_text", "")
            if not raw_text:
                raise ValueError("Could not extract readable text from paper for question answering.")
            chunk_texts = [raw_text]
            chunks_meta = [{"chunk_index": 0, "char_count": len(raw_text), "text": raw_text}]
        else:
            chunk_texts = [c.get("text", "") for c in chunks_meta]

        start_time = time.time()

        # Step 1: Lexical & semantic chunk retrieval via TF-IDF
        try:
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(chunk_texts)
            query_vec = vectorizer.transform([cleaned_question])
            similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
            
            # Rank chunk indices by similarity descending
            ranked_indices = similarities.argsort()[::-1]
        except Exception as e:
            logger.warning(f"TF-IDF vectorization warning: {e}. Defaulting to first chunks.")
            ranked_indices = list(range(min(top_k, len(chunk_texts))))
            similarities = [0.5] * len(chunk_texts)

        # Select top-k chunks
        selected_indices = ranked_indices[: min(top_k, len(chunk_texts))]
        retrieved_snippets = []
        referenced_chunks = []

        for idx in selected_indices:
            score = float(similarities[idx]) if idx < len(similarities) else 0.0
            snippet = chunk_texts[idx]
            retrieved_snippets.append(snippet)
            referenced_chunks.append({
                "chunk_index": int(chunks_meta[idx].get("chunk_index", idx)),
                "similarity_score": round(score, 3),
                "preview": snippet[:180] + ("..." if len(snippet) > 180 else ""),
            })

        # Combine retrieved context, capped at ~2000 characters to fit FLAN-T5 comfortably
        combined_context = "\n---\n".join(retrieved_snippets)[:2200]

        # Step 2: Grounded Prompt construction for FLAN-T5
        prompt = (
            f"Answer the following question about the research paper based strictly on the provided context.\n"
            f"If the answer cannot be found in the context, give the best summary of related information from the text.\n\n"
            f"Paper Context:\n{combined_context}\n\n"
            f"Question: {cleaned_question}\n\n"
            f"Direct Answer:"
        )

        # Step 3: Run FLAN-T5 inference under hardware lock
        with _QA_LOCK:
            try:
                flan_t5_summarizer.load_model()
                import torch

                device = flan_t5_summarizer.device
                tokenizer = flan_t5_summarizer.tokenizer
                model = flan_t5_summarizer.model

                inputs = tokenizer(
                    prompt,
                    return_tensors="pt",
                    max_length=1024,
                    truncation=True,
                ).to(device)

                with torch.no_grad():
                    output_ids = model.generate(
                        inputs["input_ids"],
                        attention_mask=inputs.get("attention_mask"),
                        max_length=180,
                        min_length=20,
                        num_beams=3,
                        length_penalty=1.2,
                        early_stopping=True,
                        no_repeat_ngram_size=3,
                    )

                raw_answer = tokenizer.decode(
                    output_ids[0],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True,
                ).strip()

            finally:
                # Immediate VRAM purging to preserve GPU stability
                flan_t5_summarizer.unload_model()

        latency = round(time.time() - start_time, 2)

        return {
            "question": cleaned_question,
            "answer": raw_answer,
            "referenced_chunks": referenced_chunks,
            "context_chunks_used": len(selected_indices),
            "latency_seconds": latency,
            "model": "google/flan-t5-base",
        }


qa_service = QAService()
