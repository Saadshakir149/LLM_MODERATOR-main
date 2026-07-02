"""
server/moderator_engine.py
===========================
Master Orchestrator Engine for the Voice LLM Moderator.
Integrates:
1. Self-Healing STT & Intent Classification
2. Dynamic Room/User State Management
3. RAG Intervention Exemplar Retrieval
4. Dynamic Prompt Building
5. LLM Response Generation & Semantic Deduplication
6. Structured Supabase Intervention Logging
"""

import time
import logging
from typing import Dict, Any, List, Optional
import numpy as np

from intent_classifier import get_intent_classifier
from state_manager import get_room_session_state
from rag_retriever import get_rag_retriever
from prompt_builder import DynamicPromptBuilder

logger = logging.getLogger("moderator-engine")

class ModeratorEngine:
    """Master Orchestrator combining NLP, RAG, State Tracking & Safety."""

    def __init__(self):
        self.intent_classifier = get_intent_classifier()
        self.rag_retriever = get_rag_retriever()
        self.recent_responses: Dict[str, List[str]] = {}  # room_id -> recent moderator messages

    def process_message(
        self,
        room_id: str,
        sender: str,
        message_text: str,
        language: str = "ur",
        time_remaining_min: float = 15.0
    ) -> Dict[str, Any]:
        """Process incoming user message and determine if/how to intervene."""
        start_time = time.time()
        
        # 1. Classify Intent
        intent_data = self.intent_classifier.classify(message_text, language=language)
        intent = intent_data["intent"]
        confidence = intent_data["confidence"]
        logger.info("Message from %s classified as intent='%s' (conf=%.2f)", sender, intent, confidence)

        # 2. Update Room State
        room_state_obj = get_room_session_state(room_id)
        room_state_obj.register_message(sender, intent)
        room_state_obj.update_stage(15.0 - time_remaining_min)
        state_summary = room_state_obj.summary()

        # 3. Check for Interventions Needed
        target_intent = intent
        target_user = sender

        # Overrides for group-level interventions
        dominant_user = room_state_obj.get_dominant_user()
        silent_user = room_state_obj.get_silent_user()

        if intent == "normal":
            if silent_user and (time.time() - room_state_obj.last_intervention_time) > 90.0:
                target_intent = "participation_balance"
                target_user = silent_user
            elif time_remaining_min <= 3.0 and (time.time() - room_state_obj.last_intervention_time) > 120.0:
                target_intent = "time_urgency"
                target_user = None

        # 4. RAG Exemplar Retrieval
        exemplars = self.rag_retriever.retrieve(intent=target_intent, language=language, top_k=2)

        # 5. Build Dynamic Prompt
        system_prompt = DynamicPromptBuilder.build_prompt(
            room_state=state_summary,
            target_intent=target_intent,
            target_user=target_user,
            rag_exemplars=exemplars,
            language=language,
            time_remaining_min=time_remaining_min
        )

        # 6. Call LLM
        candidate_response = self._generate_llm_response(system_prompt, message_text, language)

        # 7. Semantic Response Deduplication
        final_response = self._deduplicate_response(room_id, candidate_response, system_prompt, message_text, language)

        # Record recent response
        if room_id not in self.recent_responses:
            self.recent_responses[room_id] = []
        self.recent_responses[room_id].append(final_response)
        if len(self.recent_responses[room_id]) > 5:
            self.recent_responses[room_id].pop(0)

        latency = round(time.time() - start_time, 3)
        room_state_obj.last_intervention_time = time.time()

        # 8. Return Intervention Result
        return {
            "response_text": final_response,
            "intervention_type": target_intent,
            "target_user": target_user,
            "confidence": confidence,
            "latency_seconds": latency,
            "room_state": state_summary
        }

    def _generate_llm_response(self, system_prompt: str, user_text: str, language: str) -> str:
        """Call LLM via OpenAI / Groq fallback."""
        try:
            from prompts import call_llm
            response = call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                max_tokens=100
            )
            return response.strip()
        except Exception as e:
            logger.error("Error in call_llm: %s", e)
            if language == "ur":
                return "Aap sab ka khayal buhat ahem hai. Aayein mil kar next item ko discuss karein."
            return "Thank you for sharing. Let's continue discussing the next item together."

    def _deduplicate_response(self, room_id: str, candidate: str, system_prompt: str, user_text: str, language: str) -> str:
        """Ensure candidate response is not semantically repetitive."""
        recents = self.recent_responses.get(room_id, [])
        if not recents:
            return candidate

        # Check for phrase overlap or high similarity
        candidate_lower = candidate.lower()
        for prev in recents:
            if candidate_lower in prev.lower() or prev.lower() in candidate_lower:
                logger.warning("Repetitive response detected. Regenerating response...")
                try:
                    from prompts import call_llm
                    retry_prompt = system_prompt + "\nIMPORTANT: Avoid using phrasing similar to: " + prev
                    new_resp = call_llm(
                        messages=[
                            {"role": "system", "content": retry_prompt},
                            {"role": "user", "content": user_text}
                        ],
                        temperature=0.85
                    )
                    return new_resp.strip()
                except Exception as ex:
                    logger.error("Deduplication regeneration error: %s", ex)
                    break
        return candidate


# Global Engine Singleton
_moderator_engine_instance = None

def get_moderator_engine() -> ModeratorEngine:
    global _moderator_engine_instance
    if _moderator_engine_instance is None:
        _moderator_engine_instance = ModeratorEngine()
    return _moderator_engine_instance
