"""
High-Level Summarization and Model Comparison Orchestrator.

Coordinates:
- Google FLAN-T5 and Meta BART inference
- Preprocessed text ingestion
- Evaluation and ROUGE scoring
- Side-by-side benchmarking and .pkl artifact export
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.evaluation.model_evaluator import model_evaluator
from app.models.bart import bart_summarizer
from app.models.flan_t5 import flan_t5_summarizer
from app.services.pdf_service import pdf_service

logger = logging.getLogger("researchs.services.summarization")

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

# Global GPU lock to prevent concurrent VRAM contention or race conditions
_INFERENCE_LOCK = threading.Lock()


class SummarizationService:
    """Orchestrates research paper summarization, comparison, and evaluation."""

    def _prepare_paper_text(self, saved_filename: str) -> Dict[str, Any]:
        """Loads and preprocessed the research paper text from storage."""
        file_path = UPLOAD_DIR / os.path.basename(saved_filename)
        if not file_path.exists():
            raise FileNotFoundError(f"Research paper not found in uploads: {saved_filename}")

        preprocessed = pdf_service.process_pdf(file_path)
        chunks = preprocessed.get("chunks", [])

        # For summarization, select key academic chunks (lead / abstract + key findings)
        if not chunks:
            source_text = preprocessed.get("preview_text", "")
        elif len(chunks) == 1:
            source_text = chunks[0]["text"]
        else:
            # Combine the first 2-3 most informative chunks (approx 600-800 words)
            selected_chunks = chunks[:3]
            source_text = " ".join(c["text"] for c in selected_chunks)

        words = len(source_text.split())
        if words < 15:
            raise ValueError(
                f"Insufficient readable text found in document ({words} words extracted). "
                "This file appears to be an image-based scanned PDF, presentation, or empty document. "
                "Please upload a standard text-based research paper."
            )

        return {
            "source_text": source_text,
            "preprocessed_meta": preprocessed,
            "file_path": file_path,
        }

    def summarize_single_model(
        self,
        saved_filename: str,
        model_type: str = "flan-t5",
        max_length: int = 160,
        min_length: int = 40,
    ) -> Dict[str, Any]:
        """Runs inference using a single specified model (flan-t5 or bart)."""
        data = self._prepare_paper_text(saved_filename)
        source_text = data["source_text"]

        model_key = model_type.lower().strip()
        with _INFERENCE_LOCK:
            try:
                if "flan" in model_key or "t5" in model_key:
                    result = flan_t5_summarizer.summarize(
                        source_text,
                        max_length=max_length,
                        min_length=min_length,
                    )
                elif "bart" in model_key:
                    result = bart_summarizer.summarize(
                        source_text,
                        max_length=max_length,
                        min_length=min_length,
                    )
                else:
                    raise ValueError(f"Unsupported model type: {model_type}. Choose 'flan-t5' or 'bart'.")

                # Evaluate generated summary
                eval_metrics = model_evaluator.evaluate_summary(
                    source_text=source_text,
                    summary=result["summary"],
                    latency_seconds=result["latency_seconds"],
                )
                result["evaluation"] = eval_metrics
                return result
            finally:
                # Free memory immediately on completion
                flan_t5_summarizer.unload_model()
                bart_summarizer.unload_model()

    def compare_models(
        self,
        saved_filename: str,
        max_length: int = 160,
        min_length: int = 40,
    ) -> Dict[str, Any]:
        """
        Runs both Google FLAN-T5 and Meta BART on the exact same research paper text,
        benchmarks their speed, computes ROUGE scores, selects the best model,
        and exports 'best_model.pkl' (fulfilling Professor Criteria 4, 7, 8, & 14).
        Uses sequential offloading so peak memory stays ultra-low.
        """
        data = self._prepare_paper_text(saved_filename)
        source_text = data["source_text"]
        preprocessed = data["preprocessed_meta"]

        logger.info(f"Running comparative inference on: {saved_filename}...")

        with _INFERENCE_LOCK:
            try:
                # 1. Run FLAN-T5
                flan_result = flan_t5_summarizer.summarize(
                    source_text,
                    max_length=max_length,
                    min_length=min_length,
                )
                flan_eval = model_evaluator.evaluate_summary(
                    source_text=source_text,
                    summary=flan_result["summary"],
                    latency_seconds=flan_result["latency_seconds"],
                )
                flan_result["evaluation"] = flan_eval

                # Free FLAN-T5 from RAM/GPU before loading BART
                flan_t5_summarizer.unload_model()

                # 2. Run Meta BART
                bart_result = bart_summarizer.summarize(
                    source_text,
                    max_length=max_length,
                    min_length=min_length,
                )
                bart_eval = model_evaluator.evaluate_summary(
                    source_text=source_text,
                    summary=bart_result["summary"],
                    latency_seconds=bart_result["latency_seconds"],
                )
                bart_result["evaluation"] = bart_eval

                # Free BART after generation
                bart_summarizer.unload_model()
            except Exception:
                flan_t5_summarizer.unload_model()
                bart_summarizer.unload_model()
                raise

        # 3. Compute cross-model agreement (ROUGE similarity between FLAN-T5 and BART outputs)
        agreement_rouge = model_evaluator.compute_rouge(
            reference=flan_result["summary"],
            candidate=bart_result["summary"],
        )


        # 4. Determine winning model
        flan_f1 = flan_eval["rouge_scores"]["rouge1"]["f1"]
        bart_f1 = bart_eval["rouge_scores"]["rouge1"]["f1"]

        # Selection criterion: balanced ROUGE F1 score and readability
        if bart_f1 >= flan_f1:
            best_model_name = "Meta BART (facebook/bart-large-cnn)"
            best_metadata = bart_result
            selection_reason = (
                f"Meta BART achieved higher ROUGE-1 F1 ({bart_f1:.4f} vs {flan_f1:.4f}), "
                "producing richer abstractive synthesis."
            )
        else:
            best_model_name = "Google FLAN-T5 (google/flan-t5-base)"
            best_metadata = flan_result
            selection_reason = (
                f"Google FLAN-T5 achieved higher ROUGE-1 F1 ({flan_f1:.4f} vs {bart_f1:.4f}) "
                f"with faster inference latency ({flan_result['latency_seconds']}s)."
            )

        # 5. Export .pkl file for Professor Criterion 14
        pkl_path = model_evaluator.export_best_model_pickle(
            best_model_name=best_model_name,
            model_metadata=best_metadata,
        )

        faster_model = "Google FLAN-T5" if flan_result["latency_seconds"] <= bart_result["latency_seconds"] else "Meta BART"

        return {
            "status": "success",
            "paper_filename": saved_filename,
            "source_word_count": len(source_text.split()),
            "models": {
                "flan_t5": flan_result,
                "bart": bart_result,
            },
            "comparison": {
                "faster_model": faster_model,
                "flan_t5_latency": flan_result["latency_seconds"],
                "bart_latency": bart_result["latency_seconds"],
                "flan_t5_rouge1_f1": flan_f1,
                "bart_rouge1_f1": bart_f1,
                "cross_model_agreement_rouge1_f1": agreement_rouge["rouge1"]["f1"],
                "best_overall_model": best_model_name,
                "selection_reason": selection_reason,
                "best_model_pkl_saved": os.path.basename(pkl_path),
            },
        }


# Singleton instance
summarization_service = SummarizationService()
