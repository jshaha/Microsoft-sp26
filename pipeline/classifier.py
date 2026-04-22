"""
DistilBERT category router.

Wraps the fine-tuned 11-class MIND classifier produced by
`Classifier/mind-bert-classifier (1).ipynb`, exported via
`model.save_pretrained(...)` + `tokenizer.save_pretrained(...)` +
`label_map.json`.
"""

from __future__ import annotations

import json
import os
from typing import List, Dict, Optional

import numpy as np
import torch
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
)


class CategoryClassifier:
    """Wraps the DistilBERT MIND classifier for inference only."""

    def __init__(
        self,
        model_dir: str,
        max_len: int = 256,
        confidence_threshold: float = 0.60,
        device: Optional[str] = None,
    ):
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(
                f"Classifier directory not found: {model_dir}. "
                f"Export from the notebook with model.save_pretrained(...)."
            )

        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.max_len = max_len
        self.confidence_threshold = confidence_threshold

        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_dir)
        self.model = DistilBertForSequenceClassification.from_pretrained(
            model_dir
        ).to(self.device).eval()

        label_map_path = os.path.join(model_dir, "label_map.json")
        if os.path.exists(label_map_path):
            with open(label_map_path, "r") as f:
                lm = json.load(f)
            self.id2label = {int(k): v for k, v in lm["id2label"].items()}
        else:
            # Fallback to what HF stashed in config
            self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}

    # ------------------------------------------------------------------
    @torch.no_grad()
    def classify(
        self,
        title: str,
        abstract: str = "",
        top_k: int = 3,
    ) -> List[Dict]:
        """Return top-k predictions: [{category, confidence, uncertain}, ...]."""
        text = (title.strip() + " [SEP] " + abstract.strip()).strip()
        enc = self.tokenizer(
            text,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        ).to(self.device)

        logits = self.model(**enc).logits
        probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        top_idx = np.argsort(probs)[::-1][:top_k]
        top_conf = float(probs[top_idx[0]])
        uncertain = top_conf < self.confidence_threshold

        return [
            {
                "category": self.id2label[int(i)],
                "confidence": float(probs[int(i)]),
                "uncertain": uncertain,
            }
            for i in top_idx
        ]

    # ------------------------------------------------------------------
    def route(self, title: str, abstract: str = "") -> Dict[str, object]:
        """
        Returns the routing decision for the downstream extractor:
            {"category": str or "uncertain", "confidence": float}
        """
        top = self.classify(title, abstract, top_k=1)[0]
        if top["uncertain"]:
            return {"category": "uncertain", "confidence": top["confidence"]}
        return {"category": top["category"], "confidence": top["confidence"]}
