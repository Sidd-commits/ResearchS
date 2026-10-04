"""
Google LongT5 Model Integration for Long Academic Paper Summarization.

LongT5 (Long Text-to-Text Transfer Transformer) handles extended context
lengths up to 4096+ tokens using Transient Global (TGlobal) attention.
Designed by Google Research specifically for long document modeling.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("researchs.models.long_t5")


class LongT5Summarizer:
    """Wrapper class for Google LongT5 summarization model."""

    def __init__(self, model_name: str = "google/long-t5-tglobal-base") -> None:
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        self._is_loaded = False

    def load_model(self) -> None:
        """Loads model and tokenizer to memory (lazy loaded on first request)."""
        if self._is_loaded:
            return

        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        logger.info(f"Loading LongT5 model weights: {self.model_name}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Load in torch.float16 if GPU is available to save memory and increase speed
        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
        ).to(self.device)

        self.model.eval()
        self._is_loaded = True
        logger.info(f"LongT5 loaded successfully onto device: {self.device}")

    def unload_model(self) -> None:
        """Frees model and tokenizer from GPU and RAM."""
        if not self._is_loaded and self.model is None:
            return

        import gc
        logger.info("Unloading LongT5 model to free memory...")
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
        self._is_loaded = False
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def summarize(
        self,
        text: str,
        max_length: int = 160,
        min_length: int = 40,
        num_beams: int = 4,
        length_penalty: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Generates an abstractive summary of input academic text using LongT5.
        LongT5 supports larger input windows (up to 4096 tokens).
        """
        if not text or not text.strip():
            return {
                "summary": "",
                "word_count": 0,
                "latency_seconds": 0.0,
                "model": self.model_name,
                "parameters": "~250M",
            }

        self.load_model()
        import torch

        start_time = time.time()

        prompt = f"summarize: {text}"

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=4096,
            truncation=True,
        ).to(self.device)

        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                length_penalty=length_penalty,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )

        summary_text = self.tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        ).strip()

        latency = round(time.time() - start_time, 2)
        word_count = len(summary_text.split())

        return {
            "summary": summary_text,
            "word_count": word_count,
            "latency_seconds": latency,
            "model": self.model_name,
            "parameters": "~250M",
            "context_window": 4096,
        }


long_t5_summarizer = LongT5Summarizer()
