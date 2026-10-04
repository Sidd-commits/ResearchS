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
from app.models.long_t5 import long_t5_summarizer
from app.services.pdf_service import pdf_service

logger = logging.getLogger("researchs.services.summarization")

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

# Global GPU lock to prevent concurrent VRAM contention or race conditions
_INFERENCE_LOCK = threading.Lock()


class SummarizationService:
    """Orchestrates research paper summarization, comparison, and evaluation."""

    def _prepare_paper_text(self, saved_filename: str, max_chunks: int = 3) -> Dict[str, Any]:
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
            # Select chunks up to max_chunks (e.g. 3 for BART/FLAN-T5, up to 8 for LongT5)
            selected_chunks = chunks[:max_chunks]
            raw_text = " ".join(c["text"] for c in selected_chunks)

            # Strip author / affiliation header if "Abstract" or "Introduction" appears in leading text
            import re
            match = re.search(r'\b(abstract|introduction)\b', raw_text, re.IGNORECASE)
            if match and match.start() < 1200:
                source_text = raw_text[match.start():]
            else:
                source_text = raw_text

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
        """Runs inference using a single specified model (flan-t5, bart, or long-t5)."""
        model_key = model_type.lower().strip()
        is_long = "long" in model_key

        # LongT5 can ingest up to 4,096 tokens, so pass up to 8 chunks (~2,000+ words)
        max_chunks = 8 if is_long else 3
        data = self._prepare_paper_text(saved_filename, max_chunks=max_chunks)
        source_text = data["source_text"]

        with _INFERENCE_LOCK:
            try:
                if is_long:
                    # Provide extended generation length (220-260 tokens) and higher beam search
                    target_max = max_length if max_length != 160 else 240
                    target_min = min_length if min_length != 40 else 70
                    result = long_t5_summarizer.summarize(
                        source_text,
                        max_length=target_max,
                        min_length=target_min,
                        num_beams=4,
                        length_penalty=1.8,
                    )
                elif "flan" in model_key or "t5" in model_key:
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
                    raise ValueError(f"Unsupported model type: {model_type}. Choose 'flan-t5', 'bart', or 'long-t5'.")

                # Evaluate generated summary
                eval_metrics = model_evaluator.evaluate_summary(
                    source_text=source_text,
                    summary=result["summary"],
                    latency_seconds=result["latency_seconds"],
                )
                result["evaluation"] = eval_metrics
                result["input_words_analyzed"] = len(source_text.split())
                return result
            finally:
                # Free memory immediately on completion
                flan_t5_summarizer.unload_model()
                bart_summarizer.unload_model()
                long_t5_summarizer.unload_model()

    def compare_models(
        self,
        saved_filename: str,
        max_length: int = 180,
        min_length: int = 40,
    ) -> Dict[str, Any]:
        """
        Runs Google FLAN-T5, Meta BART, and Google LongT5 on the exact same research paper text,
        benchmarks their speed, computes ROUGE scores, selects the best model,
        and exports 'best_model.pkl' (fulfilling Professor Criteria 4, 7, 8, & 14).
        Uses sequential offloading so peak memory stays ultra-low.
        """
        data = self._prepare_paper_text(saved_filename, max_chunks=4)
        source_text = data["source_text"]
        preprocessed = data["preprocessed_meta"]

        logger.info(f"Running comparative inference (FLAN-T5, BART, LongT5) on: {saved_filename}...")

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
                bart_summarizer.unload_model()

                # 3. Run Google LongT5 (Transient Global Attention)
                long_t5_result = long_t5_summarizer.summarize(
                    source_text,
                    max_length=max_length,
                    min_length=min_length,
                )
                long_t5_eval = model_evaluator.evaluate_summary(
                    source_text=source_text,
                    summary=long_t5_result["summary"],
                    latency_seconds=long_t5_result["latency_seconds"],
                )
                long_t5_result["evaluation"] = long_t5_eval
                long_t5_summarizer.unload_model()

            except Exception:
                flan_t5_summarizer.unload_model()
                bart_summarizer.unload_model()
                long_t5_summarizer.unload_model()
                raise

        # 4. Compute cross-model agreement
        agreement_flan_bart = model_evaluator.compute_rouge(
            reference=flan_result["summary"],
            candidate=bart_result["summary"],
        )
        agreement_bart_longt5 = model_evaluator.compute_rouge(
            reference=bart_result["summary"],
            candidate=long_t5_result["summary"],
        )

        # 5. Determine winning model across all 3 architectures
        flan_f1 = flan_eval["rouge_scores"]["rouge1"]["f1"]
        bart_f1 = bart_eval["rouge_scores"]["rouge1"]["f1"]
        longt5_f1 = long_t5_eval["rouge_scores"]["rouge1"]["f1"]

        candidates = [
            {
                "name": "Meta BART (facebook/bart-large-cnn)",
                "display": "Meta BART",
                "result": bart_result,
                "f1": bart_f1,
                "latency": bart_result["latency_seconds"],
                "reason": (
                    f"Meta BART achieved the highest ROUGE-1 F1 ({bart_f1:.4f}), "
                    "producing rich abstractive narrative synthesis."
                ),
            },
            {
                "name": "Google FLAN-T5 (google/flan-t5-base)",
                "display": "Google FLAN-T5",
                "result": flan_result,
                "f1": flan_f1,
                "latency": flan_result["latency_seconds"],
                "reason": (
                    f"Google FLAN-T5 achieved high ROUGE-1 F1 ({flan_f1:.4f}) "
                    f"with fast instruction-tuned Seq2Seq inference ({flan_result['latency_seconds']}s)."
                ),
            },
            {
                "name": "Google LongT5 (google/long-t5-tglobal-base)",
                "display": "Google LongT5",
                "result": long_t5_result,
                "f1": longt5_f1,
                "latency": long_t5_result["latency_seconds"],
                "reason": (
                    f"Google LongT5 achieved the highest ROUGE-1 F1 ({longt5_f1:.4f}) "
                    "leveraging Transient Global Attention for extended scientific text."
                ),
            },
        ]

        best = max(candidates, key=lambda c: c["f1"])
        best_model_name = best["name"]
        best_metadata = best["result"]
        selection_reason = best["reason"]

        fastest = min(candidates, key=lambda c: c["latency"])
        faster_model = fastest["display"]

        # 6. Export .pkl file for Professor Criterion 14
        pkl_path = model_evaluator.export_best_model_pickle(
            best_model_name=best_model_name,
            model_metadata=best_metadata,
        )

        return {
            "status": "success",
            "paper_filename": saved_filename,
            "source_word_count": len(source_text.split()),
            "models": {
                "flan_t5": flan_result,
                "bart": bart_result,
                "long_t5": long_t5_result,
            },
            "comparison": {
                "faster_model": faster_model,
                "flan_t5_latency": flan_result["latency_seconds"],
                "bart_latency": bart_result["latency_seconds"],
                "long_t5_latency": long_t5_result["latency_seconds"],
                "flan_t5_rouge1_f1": flan_f1,
                "bart_rouge1_f1": bart_f1,
                "long_t5_rouge1_f1": longt5_f1,
                "cross_model_agreement_rouge1_f1": agreement_flan_bart["rouge1"]["f1"],
                "cross_model_agreement_bart_longt5_rouge1_f1": agreement_bart_longt5["rouge1"]["f1"],
                "best_overall_model": best_model_name,
                "selection_reason": selection_reason,
                "best_model_pkl_saved": os.path.basename(pkl_path),
            },
        }


# Singleton instance
summarization_service = SummarizationService()
