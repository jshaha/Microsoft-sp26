"""
Category-routed Qwen2.5 entity + affect extractor (Mixture-of-Experts).

Each fine-tuned LoRA adapter is paired with the same base Qwen model
(`Qwen/Qwen2.5-0.5B-Instruct` by default). Only the finance adapter is
fine-tuned today; other categories fall back to the base model with the
same prompt (still returns valid JSON, just less category-specialised).
"""

from __future__ import annotations

import json
import os
import re
from typing import List, Dict, Optional, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

try:
    from peft import PeftModel
    _HAS_PEFT = True
except ImportError:  # PEFT only needed when loading adapters
    _HAS_PEFT = False

from .schemas import EntityAffect


# ---------------------------------------------------------------------------
FINANCE_ENTITY_TYPES = [
    "Company", "FinancialInstrument", "EconomicIndicator", "MarketIndex",
    "Currency", "FinancialEvent", "Person", "Ticker", "Sector", "Asset",
    "Commodity", "Index", "Country_or_Region", "GovernmentBody",
    "CentralBank", "FinancialInstitution", "MacroIndicator",
    "MicroIndicator", "Policy_or_Regulation",
]

GENERIC_ENTITY_TYPES = [
    "Person", "Organization", "Location", "Product", "Event", "Topic",
]

DEFAULT_SYSTEM_PROMPT = (
    "You are a news NLP system. Follow the user's task exactly. "
    "When asked to extract entities, use only the entity types "
    "provided. sentiment must be one of: positive, neutral, negative. "
    "valence must be a float in [-1.0, 1.0]. arousal must be a float in "
    "[0.0, 1.0]. Return strict JSON only when the user asks for JSON."
)


# ---------------------------------------------------------------------------
class EntityAffectExtractor:
    """One category = one expert. Wraps a Qwen base model + optional LoRA."""

    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
        adapter_dir: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        device: Optional[str] = None,
        max_new_tokens: int = 400,
    ):
        self.base_model_name = base_model_name
        self.adapter_dir = adapter_dir
        self.entity_types = entity_types or GENERIC_ENTITY_TYPES
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.max_new_tokens = max_new_tokens

        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_name, trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        dtype = (
            torch.bfloat16
            if self.device.type == "cuda" and torch.cuda.is_bf16_supported()
            else torch.float32
        )

        base = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=dtype,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )

        if adapter_dir:
            if not _HAS_PEFT:
                raise ImportError(
                    "peft is required to load a LoRA adapter. "
                    "`pip install peft`."
                )
            self.model = PeftModel.from_pretrained(base, adapter_dir)
        else:
            self.model = base

        self.model.to(self.device).eval()

    # ------------------------------------------------------------------
    def _build_prompt(self, article: str, num_entities: int) -> str:
        user_prompt = (
            f"Task: extract_entities_and_affect\n"
            f"Extract up to {num_entities} relevant entities from the article.\n\n"
            f"Use only these entity types:\n{self.entity_types}\n\n"
            f"For each entity, return: text, type, sentiment, valence, "
            f"arousal, evidence.\n\n"
            f"Return strict JSON only with this schema:\n"
            f'{{"entities": [{{"text": "...", "type": "...", '
            f'"sentiment": "positive|neutral|negative", '
            f'"valence": 0.0, "arousal": 0.0, "evidence": "..."}}]}}'
            f"\n\nArticle:\n{article}"
        )
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """Locate the first top-level JSON object in `raw`."""
        # Prefer fenced code blocks first
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if fence:
            candidate = fence.group(1)
        else:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return {"entities": []}
            candidate = raw[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return {"entities": []}

    # ------------------------------------------------------------------
    @torch.no_grad()
    def extract(
        self,
        article: str,
        num_entities: int = 5,
    ) -> List[EntityAffect]:
        prompt = self._build_prompt(article, num_entities)

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            temperature=1.0,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        gen = output[0, inputs["input_ids"].shape[1] :]
        raw = self.tokenizer.decode(gen, skip_special_tokens=True)

        obj = self._parse_json(raw)
        entities_raw = obj.get("entities", []) or []
        entities: List[EntityAffect] = []
        for e in entities_raw:
            try:
                ent = EntityAffect.from_dict(e)
                # Clamp to spec range
                ent.valence = max(-1.0, min(1.0, ent.valence))
                ent.arousal = max(0.0, min(1.0, ent.arousal))
                entities.append(ent)
            except Exception:
                continue
        return entities


# ---------------------------------------------------------------------------
class EntityExtractorRegistry:
    """Mixture-of-Experts router: category -> extractor."""

    def __init__(self, default: Optional[EntityAffectExtractor] = None):
        self._experts: Dict[str, EntityAffectExtractor] = {}
        self._default = default

    def register(self, category: str, extractor: EntityAffectExtractor) -> None:
        self._experts[category.lower()] = extractor

    def set_default(self, extractor: EntityAffectExtractor) -> None:
        self._default = extractor

    def has(self, category: str) -> bool:
        return category.lower() in self._experts

    def get(self, category: str) -> EntityAffectExtractor:
        expert = self._experts.get(category.lower())
        if expert is not None:
            return expert
        if self._default is not None:
            return self._default
        raise KeyError(
            f"No extractor registered for category '{category}' and no "
            f"default set."
        )

    def extract(
        self,
        category: str,
        article: str,
        num_entities: int = 5,
    ) -> List[EntityAffect]:
        return self.get(category).extract(article, num_entities=num_entities)
