"""
server/prompt_builder.py
========================
Dynamic System Prompt Builder for the LLM Moderator.
Assembles tailored, state-aware system prompts injected with real-time room metrics,
intent flags, stage urgency guidance, and RAG intervention exemplars.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("prompt-builder")

STAGE_DIRECTIVES = {
    "initial": "0-5 minutes (Brainstorming Phase): Encourage all participants to share their initial thoughts. Do not push for final consensus yet.",
    "consensus": "5-12 minutes (Consensus Building Phase): Identify areas of agreement and disagreement. Encourage quiet participants to contribute.",
    "finalizing": "12-15 minutes (Finalization Phase): Push gently for a locked group consensus on rankings 1 through 12."
}

class DynamicPromptBuilder:
    """Constructs dynamic prompts for the voice LLM Moderator."""

    @staticmethod
    def build_prompt(
        room_state: Dict[str, Any],
        target_intent: str,
        target_user: Optional[str],
        rag_exemplars: List[Dict[str, Any]],
        language: str = "ur",
        time_remaining_min: float = 15.0
    ) -> str:
        """Construct the prompt incorporating room state and retrieved RAG exemplars."""
        lang_name = "Roman Urdu (Latin script)" if language == "ur" else "English"
        
        prompt_parts = [
            f"You are the AI Moderator for a collaborative Desert Survival ranking session.",
            f"PRIMARY LANGUAGE CONSTRAINT: Speak ONLY in {lang_name}.",
            "Rules for speech:",
            "- Be concise, encouraging, and clear (max 40-50 words).",
            "- Never repeat the exact same phrase multiple times.",
            "- Avoid robotic phrase starters like 'Ek choti si baat'. Use natural conversational phrasing."
        ]

        stage = room_state.get("stage", "initial")
        stage_guide = STAGE_DIRECTIVES.get(stage, STAGE_DIRECTIVES["initial"])
        prompt_parts.append(f"\nROOM STATE SUMMARY:")
        prompt_parts.append(f"- Current Stage: {stage.upper()} ({stage_guide})")
        prompt_parts.append(f"- Time Remaining: {time_remaining_min:.1f} minutes")
        
        user_states = room_state.get("users", {})
        if user_states:
            prompt_parts.append("- Participant Statuses:")
            for uname, udata in user_states.items():
                status_str = []
                if udata.get("completed_ranking"):
                    status_str.append("COMPLETED RANKING")
                if udata.get("refused_ranking"):
                    status_str.append("REFUSED RANKING")
                msg_cnt = udata.get("message_count", 0)
                status_str.append(f"{msg_cnt} msgs")
                prompt_parts.append(f"  * {uname}: {', '.join(status_str)}")

        prompt_parts.append("\nPRIMARY INTERVENTION OBJECTIVE:")
        if target_intent == "ranking_complete":
            prompt_parts.append(
                f"- User {target_user} explicitly stated they FINISHED ranking. "
                "DO NOT ask them to rank again! Acknowledge their completion and invite the group to review item rankings together."
            )
        elif target_intent == "ranking_refusal":
            prompt_parts.append(
                f"- User {target_user} expressed hesitation or refusal to rank. "
                "Be warm and non-pressuring. Ask them to share just their top 1 item choice."
            )
        elif target_intent == "participation_balance":
            prompt_parts.append(
                f"- User {target_user} has been quiet. Gently invite {target_user} to share their opinion on the current item."
            )
        elif target_intent == "conflict":
            prompt_parts.append(
                "- Hostility or argument detected. De-escalate calmly, validate team effort, and refocus attention on item evaluation."
            )
        elif target_intent == "time_urgency":
            prompt_parts.append(
                f"- Only {time_remaining_min:.1f} minutes remain. Prompt the team to finalize their top 12 consensus list now."
            )
        else:
            prompt_parts.append("- Facilitate constructive discussion toward item ranking consensus.")

        if rag_exemplars:
            prompt_parts.append("\nRECOMMENDED STRATEGY EXEMPLARS (Use as inspiration, do not copy verbatim):")
            for ex in rag_exemplars:
                prompt_parts.append(f"- Strategy: {ex.get('strategy')}")
                prompt_parts.append(f"  Exemplar Response: \"{ex.get('exemplar')}\"")

        return "\n".join(prompt_parts)
