#!/usr/bin/env python3
"""
wer_sample.py — Spot-check transcription accuracy (Word Error Rate) for voice messages.

Pulls N random rows from the `voice_recordings` table and, for each, prints the raw
transcript next to a SHORT-LIVED Supabase signed URL for the audio object (the bucket
stays private — no public URLs). A human listens to the clip, compares it to the
transcript, and tallies WER by hand.

Usage:
    python scripts/wer_sample.py            # 10 samples, 10-min URLs
    python scripts/wer_sample.py -n 25 --expires 900
    python scripts/wer_sample.py --bucket voice-recordings

Env:
    SUPABASE_URL, SUPABASE_SERVICE_KEY   (required; loaded by supabase_client)
    AUDIO_BUCKET                         (default: voice-recordings)

Assumed `voice_recordings` columns (resolved flexibly):
    transcript|text                      -> the STT transcript
    storage_path|audio_path|path|object_path|file_path  -> object path inside the bucket
    bucket                               -> optional per-row bucket override
    id, room_id, username, created_at    -> printed as context when present
"""
from __future__ import annotations

import os
import sys
import argparse
import random

# Allow running from anywhere: make the server/ dir importable for supabase_client.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from supabase_client import supabase
except Exception as e:  # pragma: no cover - import/credentials failure
    print(f"❌ Could not initialize Supabase client: {e}", file=sys.stderr)
    sys.exit(1)

_TRANSCRIPT_KEYS = ("transcript", "text", "stt_text", "transcription")
_PATH_KEYS = ("storage_path", "audio_path", "path", "object_path", "file_path", "object_key")


def _first_present(row: dict, keys) -> str | None:
    for k in keys:
        v = row.get(k)
        if v not in (None, ""):
            return str(v)
    return None


def fetch_recordings(limit_pool: int = 500) -> list[dict]:
    """Fetch a pool of voice_recordings rows to sample from."""
    try:
        resp = (
            supabase.table("voice_recordings")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit_pool)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print(
            f"❌ Could not read `voice_recordings` (does the table exist yet?): {e}",
            file=sys.stderr,
        )
        return []


def signed_url(bucket: str, path: str, expires_in: int) -> str | None:
    try:
        signed = supabase.storage.from_(bucket).create_signed_url(path, expires_in)
        return (
            (signed or {}).get("signedURL")
            or (signed or {}).get("signedUrl")
            or (signed or {}).get("signed_url")
        )
    except Exception as e:
        print(f"   ⚠️  signed URL failed for {bucket}/{path}: {e}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample voice recordings for WER spot-checks.")
    parser.add_argument("-n", "--count", type=int, default=10, help="number of samples (default 10)")
    parser.add_argument("--expires", type=int, default=600, help="signed URL TTL seconds (default 600)")
    parser.add_argument(
        "--bucket",
        default=os.getenv("AUDIO_BUCKET", "voice-recordings"),
        help="storage bucket (default: $AUDIO_BUCKET or voice-recordings)",
    )
    args = parser.parse_args()
    expires = max(30, min(args.expires, 3600))

    rows = fetch_recordings()
    if not rows:
        print("No voice_recordings found — nothing to sample.")
        return 0

    sample = random.sample(rows, min(args.count, len(rows)))
    print(f"🎧 WER spot-check — {len(sample)} of {len(rows)} recordings "
          f"(URLs valid {expires}s, bucket '{args.bucket}')\n")

    printed = 0
    for i, row in enumerate(sample, 1):
        transcript = _first_present(row, _TRANSCRIPT_KEYS) or "(no transcript field)"
        path = _first_present(row, _PATH_KEYS)
        bucket = row.get("bucket") or args.bucket

        rid = row.get("id")
        room_id = row.get("room_id")
        user = row.get("username")
        created = row.get("created_at")

        print(f"[{i}] id={rid} room={room_id} user={user} created={created}")
        print(f"    transcript: {transcript}")
        if not path:
            print("    audio_url : (no storage path on this row)\n")
            continue
        url = signed_url(bucket, path, expires)
        print(f"    audio_url : {url or '(unavailable)'}\n")
        printed += 1

    print(f"✅ Done. {printed} transcript/URL pair(s) with audio. "
          "Listen, compare to the transcript, and tally WER.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
