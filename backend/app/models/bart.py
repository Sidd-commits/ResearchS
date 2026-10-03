"""
Meta BART Model Integration for Abstractive Summarization.

BART (Bidirectional and Auto-Regressive Transformers) combines a bidirectional
encoder (like BERT) with an autoregressive decoder (like GPT).
Pretrained by Facebook AI and fine-tuned on CNN/DailyMail, it represents
the standard benchmark for fluid, abstractive document summarization.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("researchs.models.bart")


class BartSummarizer:
    """Wrapper class for Meta BART summarization model."""

    def __init__(self, model_name: str = "facebook/bart-large-cnn") -> None:
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
        from transformers import BartForConditionalGeneration, BartTokenizer

        logger.info(f"Loading BART model weights: {self.model_name}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.tokenizer = BartTokenizer.from_pretrained(self.model_name)
        
        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.model = BartForConditionalGeneration.from_pretrained(
            self.model_name,
            dtype=torch_dtype,
        ).to(self.device)

        self.model.eval()
        self._is_loaded = True
        logger.info(f"BART loaded successfully onto device: {self.device}")

    def summarize(
        self,
        text: str,
        max_length: int = 160,
        min_length: int = 40,
        num_beams: int = 4,
        length_penalty: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Generates an abstractive summary of input academic text using BART.
        """
        if not text or not text.strip():
            return {
                "summary": "",
                "word_count": 0,
                "latency_seconds": 0.0,
                "model": self.model_name,
            }

        self.load_model()
        import torch

        start_time = time.time()

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=1024,
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
            clean_up_tokenization_spaces=False,
        )


        latency = round(time.time() - start_time, 2)
        words = len(summary_text.split())

        return {
            "model": "Meta BART",
            "model_id": self.model_name,
            "architecture": "Encoder-Decoder (BART)",
            "summary": summary_text,
            "word_count": words,
            "char_count": len(summary_text),
            "latency_seconds": latency,
            "generation_params": {
                "max_length": max_length,
                "min_length": min_length,
                "num_beams": num_beams,
                "length_penalty": length_penalty,
                "device": self.device,
            },
        }


# Singleton instance
bart_summarizer = BartSummarizer()
