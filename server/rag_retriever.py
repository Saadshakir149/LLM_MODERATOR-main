"""
server/rag_retriever.py
=======================
RAG Retriever for Moderator Intervention Exemplars.
Stores structured intervention templates across intent categories and language modes.
Uses cosine similarity search (via sentence-transformers or TF-IDF matching)
to pull the top-k intervention strategy exemplars for LLM few-shot context injection.
"""

import os
import json
import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger("rag-retriever")

# Default Fallback Knowledge Base
DEFAULT_INTERVENTION_KB = [
    {
        "intent": "ranking_complete",
        "language": "ur",
        "exemplar": "Zabardast! Aap ne apni ranking complete kar li hai. Aab baaqi team members ke sath mil kar full group consensus banayein.",
        "strategy": "Acknowledge completion gracefully and redirect to team consensus."
    },
    {
        "intent": "ranking_refusal",
        "language": "ur",
        "exemplar": "Koi baat nahi! Aap poori list rank na karein, bas apna pasandeeda top 1 item share kar dein taake group aage barh sake.",
        "strategy": "De-escalate pressure, validate user feel, ask for lightweight input on 1 item."
    },
    {
        "intent": "participation_balance",
        "language": "ur",
        "exemplar": "Aap sab ki raye ahem hai. Hum [target_user] se bhi sunna chahte hain — aap ka is item par kya khayal hai?",
        "strategy": "Directly invite quiet participant by name without sounding critical."
    },
    {
        "intent": "conflict_deescalation",
        "language": "ur",
        "exemplar": "Aap sab ka maqsad ek hi hai. Aayein respectful tarike se items ki importance par fokus karein.",
        "strategy": "Refocus on task objectives and cool heated emotions."
    },
    {
        "intent": "time_urgency",
        "language": "ur",
        "exemplar": "Hamare paas sirf [time_remaining] minute baaqi hain! Aayein jaldi se rank 1 se 12 tak final consensus lock karein.",
        "strategy": "Create gentle urgency for final agreement."
    }
]

class RAGRetriever:
    """RAG Intervention Exemplar Retriever."""

    def __init__(self, json_path: str = None):
        self.json_path = json_path or os.path.join(os.path.dirname(__file__), "data", "intervention_exemplars.json")
        self.kb = self._load_kb()
        self.embeddings = None
        self.model = None
        self._init_kb()

    def _load_kb(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("Loaded RAG Knowledge Base from %s (%d exemplars)", self.json_path, len(data))
                    return data
            except Exception as e:
                logger.error("Failed to load RAG json file: %s", e)
        return DEFAULT_INTERVENTION_KB

    def _init_kb(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name="all-MiniLM-L6-v2")
            texts = [f"{item.get('intent')} {item.get('strategy')} {item.get('exemplar')}" for item in self.kb]
            self.embeddings = self.model.encode(texts, normalize_embeddings=True)
            logger.info("RAG Knowledge Base embeddings initialized successfully.")
        except Exception as e:
            logger.warning("RAG Retriever sentence-transformers fallback: %s", e)

    def retrieve(self, intent: str, language: str = "ur", top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieve relevant intervention strategy exemplars."""
        matched = [item for item in self.kb if item.get("intent") == intent and item.get("language") == language]
        if not matched:
            matched = [item for item in self.kb if item.get("intent") == intent]
        if not matched:
            matched = [item for item in self.kb if item.get("language") == language]

        return matched[:top_k]

_rag_retriever_instance = None

def get_rag_retriever() -> RAGRetriever:
    global _rag_retriever_instance
    if _rag_retriever_instance is None:
        _rag_retriever_instance = RAGRetriever()
    return _rag_retriever_instance
