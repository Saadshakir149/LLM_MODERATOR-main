"""
server/state_manager.py
========================
Room and Per-User State Manager for the real-time LLM Moderator.
Tracks participant intents, completion statuses, refusal flags, message counts,
dominance scores, and stage progression.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("state-manager")

class UserSessionState:
    """State record for an individual participant."""
    def __init__(self, username: str):
        self.username = username
        self.message_count: int = 0
        self.completed_ranking: bool = False
        self.refused_ranking: bool = False
        self.last_intent: str = "normal"
        self.last_active_time: float = time.time()
        self.last_invited_time: float = 0.0

    def update(self, intent: str):
        self.message_count += 1
        self.last_intent = intent
        self.last_active_time = time.time()
        if intent == "ranking_complete":
            self.completed_ranking = True
        elif intent == "ranking_refusal":
            self.refused_ranking = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "message_count": self.message_count,
            "completed_ranking": self.completed_ranking,
            "refused_ranking": self.refused_ranking,
            "last_intent": self.last_intent,
            "seconds_inactive": round(time.time() - self.last_active_time, 1)
        }


class RoomSessionState:
    """Per-room state container managing multi-user metrics."""
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.users: Dict[str, UserSessionState] = {}
        self.total_messages: int = 0
        self.conflict_count: int = 0
        self.last_intervention_time: float = 0.0
        self.start_time: float = time.time()
        self.stage: str = "initial"  # "initial" (0-5m), "consensus" (5-12m), "finalizing" (12-15m)

    def get_user(self, username: str) -> UserSessionState:
        if username not in self.users:
            self.users[username] = UserSessionState(username)
        return self.users[username]

    def register_message(self, username: str, intent: str):
        if username in ("Moderator", "System", None, ""):
            return
        user_state = self.get_user(username)
        user_state.update(intent)
        self.total_messages += 1
        if intent == "conflict":
            self.conflict_count += 1

    def update_stage(self, elapsed_minutes: float):
        if elapsed_minutes < 5:
            self.stage = "initial"
        elif elapsed_minutes < 12:
            self.stage = "consensus"
        else:
            self.stage = "finalizing"

    def get_dominant_user(self, threshold_ratio: float = 0.45) -> Optional[str]:
        """Return username of participant contributing disproportionately."""
        if self.total_messages < 5:
            return None
        for username, ustate in self.users.items():
            ratio = ustate.message_count / max(1, self.total_messages)
            if ratio >= threshold_ratio:
                return username
        return None

    def get_silent_user(self, silence_threshold_sec: float = 90.0, active_participants: List[str] = None) -> Optional[str]:
        """Return participant who has been quiet longest."""
        now = time.time()
        candidates = []
        target_list = active_participants if active_participants else list(self.users.keys())
        
        for name in target_list:
            if name in ("Moderator", "System"):
                continue
            ustate = self.get_user(name)
            if (now - ustate.last_active_time) >= silence_threshold_sec and (now - ustate.last_invited_time) >= 120.0:
                candidates.append((now - ustate.last_active_time, name))
        
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]

    def mark_user_invited(self, username: str):
        if username in self.users:
            self.users[username].last_invited_time = time.time()

    def summary(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "stage": self.stage,
            "total_messages": self.total_messages,
            "conflict_count": self.conflict_count,
            "users": {u: state.to_dict() for u, state in self.users.items()}
        }

# Global in-memory state repository
_room_session_states: Dict[str, RoomSessionState] = {}

def get_room_session_state(room_id: str) -> RoomSessionState:
    if room_id not in _room_session_states:
        _room_session_states[room_id] = RoomSessionState(room_id)
    return _room_session_states[room_id]
