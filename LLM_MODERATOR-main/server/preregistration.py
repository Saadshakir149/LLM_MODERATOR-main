from __future__ import annotations

# ============================================================
# 🔐 preregistration.py — Pre-registration lock (Final Phase, P1)
# ------------------------------------------------------------
# Loads /research/preregistration.json and enforces immutability via a SHA-256 lock.
# Once the PI finalizes the file and calls lock(), any later edit changes the hash and
# verify() reports a mismatch — so tampering during the study is detectable.
# ============================================================

import hashlib
import json
import os
from typing import Any, Dict, Optional

_DIR = os.path.dirname(os.path.abspath(__file__))
PREREG_PATH = os.path.join(_DIR, "research", "preregistration.json")
LOCK_PATH = os.path.join(_DIR, "research", "preregistration.lock")


def load_preregistration() -> Optional[Dict[str, Any]]:
    try:
        with open(PREREG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _canonical_bytes() -> Optional[bytes]:
    """Stable serialization for hashing (key-sorted, ignoring the volatile _meta block)."""
    data = load_preregistration()
    if data is None:
        return None
    clone = {k: v for k, v in data.items() if k != "_meta"}
    return json.dumps(clone, sort_keys=True, separators=(",", ":")).encode("utf-8")


def current_hash() -> Optional[str]:
    b = _canonical_bytes()
    return hashlib.sha256(b).hexdigest() if b is not None else None


def lock() -> Optional[str]:
    """Freeze the current pre-registration: write its hash to the lock sidecar."""
    h = current_hash()
    if h is None:
        return None
    with open(LOCK_PATH, "w", encoding="utf-8") as f:
        f.write(h)
    return h


def verify() -> Dict[str, Any]:
    """Report pre-registration lock status (present / locked / matches / hash)."""
    present = os.path.exists(PREREG_PATH)
    cur = current_hash()
    locked_hash = None
    if os.path.exists(LOCK_PATH):
        try:
            with open(LOCK_PATH, "r", encoding="utf-8") as f:
                locked_hash = f.read().strip()
        except Exception:
            locked_hash = None
    data = load_preregistration() or {}
    declared_locked = bool((data.get("_meta") or {}).get("locked"))
    return {
        "present": present,
        "declared_locked": declared_locked,
        "lock_file_present": locked_hash is not None,
        "current_hash": cur,
        "locked_hash": locked_hash,
        "matches": (locked_hash is not None and locked_hash == cur),
        "status": data.get("_meta", {}).get("status"),
    }
