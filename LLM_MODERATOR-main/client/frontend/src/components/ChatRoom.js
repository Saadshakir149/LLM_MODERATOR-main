// ============================================================
// ChatRoom.js - RESEARCH VERSION (Desert Survival Task)
// ============================================================
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import rehypeSanitize from "rehype-sanitize";
import { socket } from "../socket";
import {
  MdExitToApp,
  MdContentCopy,
  MdCheck,
  MdPerson,
  MdChat,
  MdCheckCircle,
  MdWarning,
  MdVolumeUp,
  MdVolumeOff,
  MdMic,
} from "react-icons/md";

// ============================================================
// 🎨 USER COLOR SYSTEM
// ============================================================
const USER_COLORS = [
  { bg: "bg-blue-50/80", border: "border-blue-150", text: "text-blue-700", accent: "bg-blue-500" },
  { bg: "bg-emerald-50/80", border: "border-emerald-150", text: "text-emerald-700", accent: "bg-emerald-500" },
  { bg: "bg-purple-50/80", border: "border-purple-150", text: "text-purple-700", accent: "bg-purple-500" },
  { bg: "bg-rose-50/80", border: "border-rose-150", text: "text-rose-700", accent: "bg-rose-500" },
  { bg: "bg-sky-50/80", border: "border-sky-150", text: "text-sky-700", accent: "bg-sky-500" },
  { bg: "bg-amber-50/80", border: "border-amber-150", text: "text-amber-700", accent: "bg-amber-500" },
];

const getUserColor = (userName, currentUserName) => {
  if (userName === currentUserName) {
    return USER_COLORS[0];
  }
  let hash = 0;
  for (let i = 0; i < userName.length; i++) {
    hash = userName.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % USER_COLORS.length;
  return USER_COLORS[index];
};

// ============================================================
// 🏜️ DESERT SURVIVAL ITEMS (for ranking)
// ============================================================
// Fallback only — server sends the pinned list via /api/desert-items?room_id=
const DESERT_ITEMS = [
  "A flashlight (4 batteries included)",
  "A map of the region",
  "A compass",
  "A large plastic sheet (6x8 feet)",
  "A box of matches",
  "A winter coat",
  "A bottle of salt tablets (1000 tablets)",
  "A small hunting knife",
  "2 quarts of water per person (6 quarts total)",
  "A cosmetic mirror",
  "A parachute (red & white, 30ft diameter)",
  "A book - 'Edible Animals of the Desert'",
];

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";

// ============================================================
// 🔤 Roman Urdu transliteration (display + storage stay Latin-only)
// ------------------------------------------------------------
// STT may return native Urdu script; the product is English / Roman Urdu only.
// We transliterate any Arabic-script text to Latin so chat never shows Urdu
// script. Common whole words get clean overrides; everything else falls back to
// a character map (imperfect — short vowels aren't written in Urdu — but always
// readable Latin, never leftover script). English/Latin text is returned as-is.
// ============================================================
// Arabic + Arabic Supplement + Presentation Forms A/B (covers Urdu script).
const URDU_SCRIPT_RE = /[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]/;

const URDU_WORD_MAP = {
  "اب": "ab", "کیا": "kya", "کرنا": "karna", "ہے": "hai", "ہیں": "hain",
  "نہیں": "nahi", "آپ": "aap", "کا": "ka", "کے": "ke", "کی": "ki",
  "خیال": "khayal", "ہم": "hum", "میں": "mein", "کرو": "karo", "کریں": "karein",
  "کرتے": "karte", "ٹھیک": "theek", "اچھا": "acha", "ہاں": "haan", "کیوں": "kyun",
  "کہاں": "kahan", "کب": "kab", "کیسے": "kaise", "بہت": "bohot", "تھوڑا": "thora",
  "پانی": "pani", "چاہیے": "chahiye", "مطلب": "matlab", "سمجھ": "samajh",
  "دیکھو": "dekho", "سنو": "suno", "چلو": "chalo", "پھر": "phir", "لیکن": "lekin",
  "مگر": "magar", "اور": "aur", "یہ": "yeh", "وہ": "woh", "کون": "kaun",
  "سب": "sab", "کچھ": "kuch", "بھی": "bhi", "تو": "to", "مجھے": "mujhe",
  "تم": "tum", "کرنے": "karne", "والا": "wala", "سہی": "sahi", "غلط": "ghalat",
  "اچھی": "achi", "ضروری": "zaroori", "پہلے": "pehle", "بعد": "baad",
};

const URDU_CHAR_MAP = {
  "آ": "aa", "ا": "a", "ب": "b", "پ": "p", "ت": "t", "ٹ": "t", "ث": "s",
  "ج": "j", "چ": "ch", "ح": "h", "خ": "kh", "د": "d", "ڈ": "d", "ذ": "z",
  "ر": "r", "ڑ": "r", "ز": "z", "ژ": "zh", "س": "s", "ش": "sh", "ص": "s",
  "ض": "z", "ط": "t", "ظ": "z", "ع": "a", "غ": "gh", "ف": "f", "ق": "q",
  "ک": "k", "گ": "g", "ل": "l", "م": "m", "ن": "n", "ں": "n", "و": "o",
  "ہ": "h", "ھ": "h", "ۀ": "h", "ۂ": "h", "ء": "", "ی": "y", "ئ": "y",
  "ے": "e", "ؤ": "o",
  // diacritics
  "َ": "a", "ِ": "i", "ُ": "u", "ّ": "", "ْ": "", "ٰ": "a",
  // punctuation + digits
  "۔": ".", "،": ",", "؟": "?", "؛": ";", "۰": "0", "۱": "1", "۲": "2",
  "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
};

const transliterateUrduWord = (word) => {
  // Split a trailing run of punctuation (Urdu or ASCII) so word-map lookups hit.
  const m = word.match(/^(.*?)([،؛؟۔!?.,:;]*)$/);
  const core = m ? m[1] : word;
  const punct = m ? m[2] : "";
  const punctRoman = [...punct].map((c) => URDU_CHAR_MAP[c] ?? c).join("");
  if (URDU_WORD_MAP[core]) return URDU_WORD_MAP[core] + punctRoman;
  let out = "";
  for (const ch of core) {
    if (ch in URDU_CHAR_MAP) out += URDU_CHAR_MAP[ch];
    else if (URDU_SCRIPT_RE.test(ch)) out += ""; // drop unmapped Urdu marks
    else out += ch; // keep Latin/English untouched
  }
  return out + punctRoman;
};

const romanizeUrdu = (text) => {
  if (!text || !URDU_SCRIPT_RE.test(text)) return text; // English / already-Latin
  return text
    .split(/(\s+)/)
    .map((tok) => (/^\s+$/.test(tok) ? tok : transliterateUrduWord(tok)))
    .join("");
};

// Parse a message's metadata whether it arrives as an object (live socket) or a
// JSON string (DB history). Returns {} when absent/unparseable.
const getMsgMeta = (msg) => {
  const meta = msg && msg.metadata;
  if (meta && typeof meta === "object") return meta;
  if (typeof meta === "string") {
    try { return JSON.parse(meta); } catch (_) { return {}; }
  }
  return {};
};

// A message is "voice" if flagged top-level (live broadcast) or in metadata (history).
const isVoiceMessage = (msg) =>
  msg?.input_mode === "voice" || getMsgMeta(msg).input_mode === "voice";

// ============================================================
// 🔊 Convert a moderator message to clean speakable text
// (strips the HTML task card and markdown markers so TTS doesn't read tags/asterisks)
// ============================================================
const toSpeechText = (raw) => {
  if (typeof raw !== "string") return "";
  let t = raw;
  t = t.replace(/<[^>]*>/g, " "); // strip HTML tags (task intro is HTML)
  t = t
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  t = t.replace(/[*_`#>|]/g, " "); // drop markdown emphasis / formatting markers
  t = t.replace(/\s+/g, " ").trim(); // collapse whitespace
  return t;
};

const MARKDOWN_COMPONENTS = {
  p: ({ children, ...rest }) => (
    <p className="mb-2 last:mb-0 text-sm leading-relaxed" {...rest}>
      {children}
    </p>
  ),
  strong: ({ children, ...rest }) => (
    <strong className="font-semibold" {...rest}>
      {children}
    </strong>
  ),
  em: ({ children, ...rest }) => (
    <em className="italic" {...rest}>
      {children}
    </em>
  ),
  ul: ({ children, ...rest }) => (
    <ul className="list-disc pl-5 space-y-1 mb-2 text-sm" {...rest}>
      {children}
    </ul>
  ),
  ol: ({ children, ...rest }) => (
    <ol className="list-decimal pl-5 space-y-1 mb-2 text-sm" {...rest}>
      {children}
    </ol>
  ),
  li: ({ children, ...rest }) => (
    <li className="leading-relaxed" {...rest}>
      {children}
    </li>
  ),
  h1: ({ children, ...rest }) => (
    <h1 className="text-lg font-bold mb-2" {...rest}>
      {children}
    </h1>
  ),
  h2: ({ children, ...rest }) => (
    <h2 className="text-base font-bold mb-2" {...rest}>
      {children}
    </h2>
  ),
  h3: ({ children, ...rest }) => (
    <h3 className="text-sm font-bold mb-1" {...rest}>
      {children}
    </h3>
  ),
  code: ({ children, ...rest }) => (
    <code className="bg-black/10 rounded px-1 text-xs font-mono" {...rest}>
      {children}
    </code>
  ),
};

function ChatMessageBody({ msg, isCurrentUser, onPlayVoice, onSpeak }) {
  // 🎤 Voice message: show a mic badge, the Roman Urdu transcript, and a ▶ button
  // to hear the original recording. The transcript is romanized at send time, but
  // we re-romanize defensively so no Urdu script ever leaks into the UI.
  if (isVoiceMessage(msg)) {
    const meta = getMsgMeta(msg);
    const transcript = romanizeUrdu(meta.roman_transcript || msg.message || "");
    const hasAudio = msg.id != null && !String(msg.id).includes("_");
    const accent = isCurrentUser ? "text-indigo-100" : "text-purple-700";
    return (
      <div className="flex items-start gap-2">
        {hasAudio && (
          <button
            type="button"
            onClick={() => onPlayVoice && onPlayVoice(String(msg.id))}
            title="Play original recording"
            className={`flex-shrink-0 mt-0.5 w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
              isCurrentUser
                ? "bg-white/20 hover:bg-white/30 text-white"
                : "bg-purple-100 hover:bg-purple-200 text-purple-700"
            }`}
          >
            ▶
          </button>
        )}
        <div className="min-w-0">
          <span
            className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide mb-0.5 ${accent}`}
          >
            🎤 Voice
          </span>
          <p className="whitespace-pre-wrap break-words text-sm italic">{transcript}</p>
        </div>
      </div>
    );
  }

  const isHtml =
    msg.content_format === "html" ||
    msg.message_type === "task" ||
    (typeof msg.message === "string" && msg.message.includes('class="task-intro"'));

  const isModerator = msg.sender === "Moderator";
  const isModeratorOrSystem = isModerator || msg.sender === "System";

  // Build the message body once, then (for Moderator) attach a ▶ Play button so it can
  // be voiced on demand — same affordance as a user voice message, and immune to the
  // browser's auto-play block since a click is a user gesture.
  let body;
  if (isHtml && typeof msg.message === "string") {
    body = (
      <div
        className="task-message-html max-w-none text-left [&_a]:text-indigo-600"
        dangerouslySetInnerHTML={{ __html: msg.message }}
      />
    );
  } else if (isModeratorOrSystem && typeof msg.message === "string" && /[*_`#[\]|]/.test(msg.message)) {
    body = (
      <div className={`max-w-none text-left ${isCurrentUser ? "text-white" : ""}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkBreaks]}
          rehypePlugins={[rehypeSanitize]}
          components={MARKDOWN_COMPONENTS}
        >
          {msg.message}
        </ReactMarkdown>
      </div>
    );
  } else {
    body = <p className="whitespace-pre-wrap break-words text-sm">{msg.message}</p>;
  }

  if (isModerator && onSpeak) {
    return (
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={() => onSpeak(msg.message)}
          title="Play the moderator's voice"
          className="flex-shrink-0 mt-0.5 w-7 h-7 rounded-full flex items-center justify-center bg-amber-100 hover:bg-amber-200 text-amber-700 transition-colors"
        >
          ▶
        </button>
        <div className="min-w-0 flex-1">{body}</div>
      </div>
    );
  }
  return body;
}

// ============================================================
// 🎯 MAIN CHATROOM COMPONENT
// ============================================================
export default function ChatRoom() {
  const { roomId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const userName = useMemo(
    () => new URLSearchParams(location.search).get("userName") || "Anonymous",
    [location.search]
  );
  // Join-time language choice (en | roman_urdu) carried from the join screen.
  const joinLanguage = useMemo(
    () => new URLSearchParams(location.search).get("language") || "",
    [location.search]
  );

  const [messages, setMessages] = useState([]);
  const [ready, setReady] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isLoadingFeedback, setIsLoadingFeedback] = useState(false);
  const [showParticipants, setShowParticipants] = useState(false);
  const [participants, setParticipants] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState("connecting");
  
  // ============================================================
  // 📊 RESEARCH STUDY STATE
  // ============================================================
  const [rankingSubmitted, setRankingSubmitted] = useState(false);
  const [languageWarning, setLanguageWarning] = useState(null);
  const languageWarningTimerRef = useRef(null);
  const processedIdsRef = useRef(new Set());
  const [showItemsPanel, setShowItemsPanel] = useState(true);
  const [desertItems, setDesertItems] = useState(() => [...DESERT_ITEMS]);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!roomId) return undefined;
    let cancelled = false;
    const q = encodeURIComponent(roomId);
    fetch(`${API_BASE}/api/desert-items?room_id=${q}`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(res.statusText))))
      .then((data) => {
        if (!cancelled && Array.isArray(data.items) && data.items.length > 0) {
          setDesertItems(data.items);
          try {
            sessionStorage.setItem(`room_${roomId}_items`, JSON.stringify(data.items));
          } catch (_) {
            /* ignore quota / private mode */
          }
        }
      })
      .catch(() => {
        if (cancelled) return;
        try {
          const cached = sessionStorage.getItem(`room_${roomId}_items`);
          if (cached) {
            const parsed = JSON.parse(cached);
            if (Array.isArray(parsed) && parsed.length > 0) {
              setDesertItems(parsed);
              return;
            }
          }
        } catch (_) {
          /* ignore */
        }
        setDesertItems([...DESERT_ITEMS]);
      });
    return () => {
      cancelled = true;
    };
  }, [roomId]);

  const dismissLanguageWarning = useCallback(() => {
    if (languageWarningTimerRef.current) {
      window.clearTimeout(languageWarningTimerRef.current);
      languageWarningTimerRef.current = null;
    }
    setLanguageWarning(null);
  }, []);

  const showLanguageWarningBanner = useCallback((text) => {
    if (languageWarningTimerRef.current) {
      window.clearTimeout(languageWarningTimerRef.current);
    }
    setLanguageWarning(text);
    languageWarningTimerRef.current = window.setTimeout(() => {
      setLanguageWarning(null);
      languageWarningTimerRef.current = null;
    }, 8000);
  }, []);

  // ============================================================
  // 🔊 LOCAL SEND SOUND
  // ============================================================
  const [sendSound] = useState(() => {
    const audio = new Audio();
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    audio.play = () => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = 523.25;
      osc.connect(gain);
      gain.connect(ctx.destination);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
      osc.start();
      osc.stop(ctx.currentTime + 0.1);
      return ctx.resume();
    };
    return audio;
  });

  // ============================================================
  // 🔊 MODERATOR VOICE PLAYBACK (auto-play; queue never overlaps)
  // ============================================================
  // Default ON: PTT is the primary interaction, so the moderator is read aloud
  // automatically. The user's first PTT press is the gesture that unlocks audio.
  const [voiceOn, setVoiceOn] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false); // drives the "Speaking" status
  const voiceOnRef = useRef(true);           // mirror for the long-lived socket handler
  const audioQueueRef = useRef([]);          // pending speech texts (FIFO)
  const audioPlayingRef = useRef(false);     // a clip is currently playing
  const spokenIdsRef = useRef(new Set());    // message ids already queued (no repeats)

  // ONE reusable <audio> element. Reusing a single element (not new Audio() each time)
  // lets us "unlock" it once on a user gesture so playback works AFTER the async /tts
  // fetch — browsers block play() that isn't tied to a gesture, which is why nothing was
  // audible before. A tiny silent clip played during the first tap blesses the element.
  const audioElRef = useRef(null);
  const audioUnlockedRef = useRef(false);

  const getAudioEl = useCallback(() => {
    if (!audioElRef.current) audioElRef.current = new Audio();
    return audioElRef.current;
  }, []);

  // Call from ANY user gesture (mic press, Play/Voice buttons) to enable audio output.
  const unlockAudio = useCallback(() => {
    if (audioUnlockedRef.current) return;
    const el = getAudioEl();
    try {
      el.src =
        "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=";
      const p = el.play();
      if (p && p.then) {
        p.then(() => { try { el.pause(); el.currentTime = 0; } catch (_) {} audioUnlockedRef.current = true; })
         .catch(() => { /* retry on next gesture */ });
      } else {
        audioUnlockedRef.current = true;
      }
    } catch (_) { /* ignore */ }
  }, [getAudioEl]);

  useEffect(() => {
    voiceOnRef.current = voiceOn;
  }, [voiceOn]);

  const stopAndClearVoice = useCallback(() => {
    audioQueueRef.current = [];
    const el = audioElRef.current;
    if (el) { try { el.pause(); } catch (_) { /* ignore */ } }
    audioPlayingRef.current = false;
    setIsSpeaking(false);
  }, []);

  // Play the next queued clip on the single element; chains via onended (no overlap).
  const playNextInQueue = useCallback(async () => {
    if (audioPlayingRef.current) return;
    const text = audioQueueRef.current.shift();
    if (text == null) { setIsSpeaking(false); return; }
    audioPlayingRef.current = true;
    setIsSpeaking(true);
    let url = null;
    try {
      const res = await fetch(`${API_BASE}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, room_id: roomId }),
      });
      if (!res.ok) throw new Error(`TTS ${res.status}`);
      const blob = await res.blob();
      url = URL.createObjectURL(blob);
      const el = getAudioEl();
      el.src = url;
      const advance = () => {
        try { URL.revokeObjectURL(url); } catch (_) { /* ignore */ }
        el.onended = null; el.onerror = null;
        audioPlayingRef.current = false;
        playNextInQueue();
      };
      el.onended = advance;
      el.onerror = advance;
      await el.play();
    } catch (e) {
      // Most likely autoplay still locked (no gesture yet) — stop, don't spam /tts.
      console.warn("🔇 Voice playback skipped (tap ▶ to play):", e?.message || e);
      if (url) { try { URL.revokeObjectURL(url); } catch (_) { /* ignore */ } }
      audioPlayingRef.current = false;
      setIsSpeaking(false);
    }
  }, [roomId, getAudioEl]);

  const enqueueModeratorSpeech = useCallback((rawText) => {
    const clean = toSpeechText(rawText);
    if (!clean) return;
    audioQueueRef.current.push(clean);
    playNextInQueue();
  }, [playNextInQueue]);

  // ▶ Manually play one moderator message NOW (clears the queue). The click is a user
  // gesture, so it unlocks audio for all subsequent auto-play too.
  const playModeratorMessage = useCallback((rawText) => {
    unlockAudio();
    audioQueueRef.current = [];
    audioPlayingRef.current = false;
    enqueueModeratorSpeech(rawText);
  }, [unlockAudio, enqueueModeratorSpeech]);

  // ▶ Play the ORIGINAL recording for a voice message (participant playback).
  const playbackAudioRef = useRef(null);
  const playVoiceMessage = useCallback((messageId) => {
    unlockAudio();
    if (!messageId) return;
    if (playbackAudioRef.current) {
      try { playbackAudioRef.current.pause(); } catch (_) { /* ignore */ }
      playbackAudioRef.current = null;
    }
    try {
      const audio = new Audio(`${API_BASE}/api/message/${messageId}/audio`);
      playbackAudioRef.current = audio;
      audio.play().catch((e) => console.warn("🔇 Voice playback failed:", e?.message || e));
    } catch (e) {
      console.warn("🔇 Voice playback error:", e?.message || e);
    }
  }, [unlockAudio]);

  // Stop audio + free blob URLs on unmount
  useEffect(() => stopAndClearVoice, [stopAndClearVoice]);

  // ============================================================
  // 💬 SEND A TURN (shared by the voice path; broadcast + attribution unchanged)
  // ============================================================
  // Emits to the SAME send_message pipeline as before. The spoken turn shows up
  // as an attributed, read-only transcript entry like any other message.
  // `voice` (optional): { audioToken, durationMs, transcript } — when present the turn
  // is tagged as voice so the server links its staged audio to this message at send time.
  const sendMessageText = useCallback((rawText, voice) => {
    const trimmed = (rawText || "").trim();
    if (!trimmed || !ready) return;

    sendSound.play().catch(() => {});

    const tempId = `temp:${userName}:${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: tempId,
        _optimistic: true,
        sender: userName,
        message: trimmed,
        timestamp: new Date().toISOString(),
      },
    ]);

    const payload = { room_id: roomId, message: trimmed, sender: userName };
    if (voice) {
      payload.metadata = {
        input_mode: "voice",
        stt_model: "gpt-4o-mini-transcribe",
        mime_type: "audio/webm",
        ...(voice.audioToken ? { audio_token: voice.audioToken } : {}),
        ...(Number.isFinite(voice.durationMs) ? { duration_ms: Math.round(voice.durationMs) } : {}),
        ...(voice.transcript ? { transcript_text: voice.transcript } : {}),
        ...(voice.language ? { language: voice.language } : {}),
        ...(Number.isFinite(voice.confidence) ? { confidence: voice.confidence } : {}),
        roman_transcript: voice.romanTranscript || trimmed,
      };
    }
    socket.emit("send_message", payload);
  }, [roomId, userName, ready, sendSound]);

  // ============================================================
  // 🎤 PUSH-TO-TALK (press & hold → record webm → release → auto-send via /stt)
  // ============================================================
  const [isRecording, setIsRecording] = useState(false); // "Listening"
  const [sttBusy, setSttBusy] = useState(false);          // "Thinking"
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const pttHeldRef = useRef(false); // true while the button is held (survives mic warmup)
  const recordStartRef = useRef(0); // ms timestamp when recording began (for duration_ms)

  const stopMediaStream = useCallback(() => {
    if (mediaStreamRef.current) {
      try { mediaStreamRef.current.getTracks().forEach((t) => t.stop()); } catch (_) { /* ignore */ }
      mediaStreamRef.current = null;
    }
  }, []);

  // POST the recorded blob to /stt and immediately send the transcript (no edit step).
  // The server returns an audio_token for the staged recording; we pass it (plus the
  // measured duration and raw transcript) so the send links the audio to this message.
  const transcribeAndSend = useCallback(async (blob, durationMs) => {
    setSttBusy(true);
    try {
      const form = new FormData();
      form.append("file", blob, "recording.webm");
      // Language hint (en | ur) from the room's choice → constrains transcription so it
      // can't auto-detect into a stray language/script.
      const sttLang = joinLanguage === "roman_urdu" ? "ur" : joinLanguage === "en" ? "en" : "";
      if (sttLang) form.append("language", sttLang);
      const res = await fetch(`${API_BASE}/stt`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`STT ${res.status}`);
      const data = await res.json();
      // `text` is the server-normalized Roman Urdu (or English); `raw_text` is the
      // faithful, unmodified STT output we preserve for research fidelity.
      const text = (data && data.text ? String(data.text) : "").trim();
      const rawText = (data && data.raw_text ? String(data.raw_text) : text).trim();
      if (text) {
        // Defensive: server already normalizes to Latin, but re-romanize in case the
        // LLM pass was skipped/failed so no Urdu script ever reaches the chat.
        const romanTranscript = romanizeUrdu(text);
        sendMessageText(romanTranscript, {
          audioToken: data && data.audio_token ? String(data.audio_token) : undefined,
          durationMs,
          transcript: rawText,
          romanTranscript,
          language: data && data.language ? String(data.language) : undefined,
          confidence: data && typeof data.confidence === "number" ? data.confidence : undefined,
        });
      } else {
        showLanguageWarningBanner("Couldn't catch that — hold the mic and try again.");
      }
    } catch (err) {
      console.warn("STT failed:", err?.message || err);
      showLanguageWarningBanner("Transcription failed — please hold the mic and try again.");
    } finally {
      setSttBusy(false);
    }
  }, [sendMessageText, showLanguageWarningBanner, joinLanguage]);

  const startRecording = useCallback(async () => {
    if (isRecording || sttBusy) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      showLanguageWarningBanner("Voice input isn't supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      mediaStreamRef.current = stream;
      // Pick an explicit, supported codec so MediaRecorder never falls back to a
      // type the server can't decode. Prefer Opus, then plain webm.
      const preferredTypes = ["audio/webm;codecs=opus", "audio/webm"];
      const chosenType =
        typeof MediaRecorder.isTypeSupported === "function"
          ? preferredTypes.find((t) => MediaRecorder.isTypeSupported(t))
          : undefined;
      // 32 kbps Opus is plenty for speech and keeps the upload small → faster STT.
      const opts = chosenType
        ? { mimeType: chosenType, audioBitsPerSecond: 32000 }
        : { audioBitsPerSecond: 32000 };
      const recorder = new MediaRecorder(stream, opts);
      audioChunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stopMediaStream();
        const blobType = recorder.mimeType || chosenType || "audio/webm";
        const blob = new Blob(audioChunksRef.current, { type: blobType });
        audioChunksRef.current = [];
        const durationMs = recordStartRef.current ? Date.now() - recordStartRef.current : null;
        recordStartRef.current = 0;
        setIsRecording(false);
        // A header-only / empty capture (first-press warmup, instant taps) is a
        // few hundred bytes and reaches /stt as a "corrupt" file. Real Opus
        // speech comfortably exceeds this floor — reject anything smaller.
        if (blob.size < 1200) {
          showLanguageWarningBanner("Recording too short — hold the mic and speak.");
          return;
        }
        transcribeAndSend(blob, durationMs);
      };
      mediaRecorderRef.current = recorder;
      // No timeslice: deliver ONE complete, properly-finalized WebM on stop().
      // A timeslice can cut mid-cluster on a short release, yielding a structurally
      // incomplete file that OpenAI rejects as "corrupted or unsupported".
      recorder.start();
      recordStartRef.current = Date.now();
      setIsRecording(true);
      // If the user already released during mic warmup, stop right away.
      if (!pttHeldRef.current) {
        try { recorder.stop(); } catch (_) { /* ignore */ }
        mediaRecorderRef.current = null;
      }
    } catch (err) {
      console.warn("Microphone access denied:", err?.name || err);
      setIsRecording(false);
      stopMediaStream();
      showLanguageWarningBanner("Microphone access was blocked. Allow it in your browser.");
    }
  }, [isRecording, sttBusy, showLanguageWarningBanner, stopMediaStream, transcribeAndSend]);

  const stopRecording = useCallback(() => {
    const rec = mediaRecorderRef.current;
    if (rec && rec.state !== "inactive") {
      try { rec.stop(); } catch (_) { /* ignore */ }
    }
    mediaRecorderRef.current = null;
  }, []);

  // Press-and-hold via pointer events (works for mouse + touch). Pointer capture
  // keeps the release (up) firing on the button even if the finger drifts off it.
  const handlePttDown = useCallback((e) => {
    e.preventDefault();
    if (!ready || sttBusy) return;
    unlockAudio(); // first mic press unlocks audio output for moderator playback
    pttHeldRef.current = true;
    try { e.currentTarget.setPointerCapture?.(e.pointerId); } catch (_) { /* ignore */ }
    startRecording();
  }, [ready, sttBusy, startRecording, unlockAudio]);

  const handlePttUp = useCallback((e) => {
    e.preventDefault();
    if (!pttHeldRef.current) return;
    pttHeldRef.current = false;
    try { e.currentTarget.releasePointerCapture?.(e.pointerId); } catch (_) { /* ignore */ }
    stopRecording();
  }, [stopRecording]);

  // Release mic if the user navigates away mid-recording
  useEffect(() => {
    return () => {
      const rec = mediaRecorderRef.current;
      if (rec && rec.state !== "inactive") {
        try { rec.stop(); } catch (_) { /* ignore */ }
      }
      stopMediaStream();
    };
  }, [stopMediaStream]);

  // ============================================================
  // ⚡ SOCKET CONNECTION & MESSAGES
  // ============================================================
  useEffect(() => {
    if (!roomId || !userName) return;

    setConnectionStatus("connecting");

    // Connection events
    socket.on("connect", () => {
      setConnectionStatus("connected");
      socket.emit("join_room", { room_id: roomId, user_name: userName, language: joinLanguage });
    });

    socket.on("disconnect", () => {
      setConnectionStatus("disconnected");
    });

    socket.on("connect_error", () => {
      setConnectionStatus("error");
    });

    // Room events
    socket.on("joined_room", () => {
      setReady(true);
      setConnectionStatus("connected");
      setParticipants(prev => {
        if (!prev.includes(userName)) {
          return [...prev, userName];
        }
        return prev;
      });
    });

    socket.on("chat_history", (data) => {
      const list = data.chat_history || [];
      processedIdsRef.current = new Set();
      for (const m of list) {
        const mid = m.id != null ? String(m.id) : `${m.sender}|${m.message}|${m.timestamp}`;
        processedIdsRef.current.add(mid);
      }
      setMessages(list);
      if (data.participants) {
        setParticipants(data.participants);
      } else {
        setParticipants([userName]);
      }
    });

    socket.on("receive_message", (data) => {
      console.log("📨 RECEIVED MESSAGE:", data);

      // 🔊 Voice: speak ALL live Moderator messages (incl. the task intro) when the
      // toggle is ON. toSpeechText strips HTML/markdown, so the intro card is read as
      // plain text in the room's language.
      if (voiceOnRef.current && data && data.sender === "Moderator") {
        const sid =
          data.id != null
            ? String(data.id)
            : `${data.sender}|${data.message}|${data.timestamp || ""}`;
        if (!spokenIdsRef.current.has(sid)) {
          spokenIdsRef.current.add(sid);
          enqueueModeratorSpeech(data.message);
        }
      }

      setMessages((prev) => {
        const mid =
          data.id != null
            ? String(data.id)
            : `${data.sender}|${data.message}|${data.timestamp || ""}`;

        const optIdx = prev.findIndex(
          (msg) =>
            msg._optimistic &&
            msg.sender === data.sender &&
            msg.message === data.message
        );
        if (optIdx >= 0) {
          if (processedIdsRef.current.has(mid)) return prev;
          processedIdsRef.current.add(mid);
          const next = [...prev];
          next[optIdx] = {
            ...data,
            timestamp: data.timestamp || next[optIdx].timestamp,
          };
          return next;
        }

        if (processedIdsRef.current.has(mid)) {
          if (data.flagged) {
            const idx = prev.findIndex(
              (msg) =>
                String(msg.id) === mid ||
                (msg.sender === data.sender && msg.message === data.message)
            );
            if (idx >= 0) {
              const next = [...prev];
              next[idx] = { ...next[idx], ...data };
              return next;
            }
          }
          console.log("⚠️ Duplicate message ignored:", mid);
          return prev;
        }

        processedIdsRef.current.add(mid);
        if (processedIdsRef.current.size > 800) {
          processedIdsRef.current = new Set(
            Array.from(processedIdsRef.current).slice(-400)
          );
        }

        const newMessage = {
          ...data,
          timestamp: data.timestamp || new Date().toISOString(),
        };
        return [...prev, newMessage];
      });
    });

    const onLanguageWarningPayload = (data) => {
      if (data?.type === "language_warning" && data.message) {
        showLanguageWarningBanner(data.message);
      }
    };
    socket.on("language_warning", onLanguageWarningPayload);
    socket.on("warning_message", onLanguageWarningPayload);

    socket.on("participants_update", (data) => {
      setParticipants(data.participants || []);
    });

    // ============================================================
    // 📊 RESEARCH STUDY SOCKET EVENTS
    // ============================================================
    socket.on("ranking_submitted", (data) => {
      if (data.success) {
        setRankingSubmitted(true);
        const successId = `local-ranking-ok-${Date.now()}`;
        processedIdsRef.current.add(successId);
        const successMsg = {
          id: successId,
          sender: "System",
          message: "✅ Final ranking recorded (from your discussion or end of session).",
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, successMsg]);
      } else {
        alert("❌ Failed to submit ranking: " + data.message);
      }
    });

    // Session ended handler
    socket.on("session_ended", (data) => {
      console.log("📨 Session ended with data:", data);
      const intended = data?.username;
      if (intended && intended !== userName) {
        return;
      }
      const feedback = data?.feedback || "Session ended. Thank you for participating!";
      navigate("/feedback", {
        state: {
          feedback,
          room_id: data?.room_id,
          studentName: userName,
          targetUsername: intended || userName,
        },
      });
      setIsLoadingFeedback(false);
    });

    // If already connected, join room immediately
    if (socket.connected) {
      socket.emit("join_room", { room_id: roomId, user_name: userName, language: joinLanguage });
    } else {
      socket.connect();
    }

    return () => {
      if (languageWarningTimerRef.current) {
        window.clearTimeout(languageWarningTimerRef.current);
        languageWarningTimerRef.current = null;
      }
      socket.off("connect");
      socket.off("disconnect");
      socket.off("connect_error");
      socket.off("joined_room");
      socket.off("chat_history");
      socket.off("receive_message");
      socket.off("participants_update");
      socket.off("ranking_submitted");
      socket.off("session_ended");
      socket.off("language_warning", onLanguageWarningPayload);
      socket.off("warning_message", onLanguageWarningPayload);
    };
  }, [roomId, userName, navigate, showLanguageWarningBanner, enqueueModeratorSpeech]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ============================================================
  // 🏁 END SESSION
  // ============================================================
  const endSession = () => {
    if (window.confirm("Are you sure you want to end this session? All participants will receive feedback.")) {
      setIsLoadingFeedback(true);
      socket.emit("end_session", { room_id: roomId, sender: userName });
    }
  };

  // ============================================================
  // 📊 RANKING MODAL COMPONENT
  // ============================================================
  // Calculate online count
  const onlineCount = Math.max(participants.length, 1);

  // Minimal PTT status: Idle / Listening / Thinking / Speaking
  const sessionStatus = isRecording
    ? "Listening"
    : sttBusy
    ? "Thinking"
    : isSpeaking
    ? "Speaking"
    : "Idle";

  return (
    <div className="flex flex-col h-screen bg-slate-50 font-body overflow-hidden select-none">
      {/* ⚠️ SYSTEM WARNING BANNERS */}
      {languageWarning && (
        <div
          className="fixed top-6 left-1/2 -translate-x-1/2 z-[60] max-w-lg w-[calc(100%-2rem)] rounded-2xl border-l-4 border-amber-500 border border-amber-200 bg-amber-50/95 backdrop-blur-md px-4 py-3.5 shadow-xl animate-float"
          role="alert"
        >
          <div className="flex items-start gap-3">
            <MdWarning className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
            <div className="flex-1">
              <h4 className="font-bold text-xs text-amber-950 uppercase tracking-wider mb-0.5">Moderator Notice</h4>
              <p className="text-xs text-amber-900 leading-relaxed font-medium">{languageWarning}</p>
            </div>
            <button
              type="button"
              onClick={dismissLanguageWarning}
              className="flex-shrink-0 text-amber-500 hover:text-amber-850 text-base font-bold px-1"
              aria-label="Dismiss warning"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* 🎪 TOPBAR NAVIGATION */}
      <div className="bg-white/90 backdrop-blur-md border-b border-slate-200/80 z-20 transition-all duration-300">
        <div className="px-4 py-3 md:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-100">
              <MdChat className="text-lg" />
            </div>
            <div>
              <h1 className="font-bold text-sm md:text-base text-slate-800 tracking-tight leading-tight">
                Desert Survival Discussion
              </h1>
              <div className="flex items-center gap-2 text-[11px] mt-0.5">
                <span className="font-semibold text-slate-450 uppercase tracking-wider">Room:</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(roomId);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="font-mono bg-slate-100 hover:bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded border border-slate-200 transition-colors flex items-center gap-1 cursor-pointer"
                  title="Click to copy Room ID"
                >
                  <span>{roomId.length > 10 ? `${roomId.substring(0, 6)}...${roomId.substring(roomId.length - 4)}` : roomId}</span>
                  {copied ? <MdCheck size={11} className="text-emerald-600" /> : <MdContentCopy size={10} />}
                </button>
                
                <span className="text-slate-300">|</span>

                <div className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-150">
                  <span className="pulse-green">
                    <span className="pulse-green-ping"></span>
                    <span className="pulse-green-dot"></span>
                  </span>
                  <span className="text-slate-600 font-semibold">{onlineCount}/3 online</span>
                </div>

                {rankingSubmitted && (
                  <span className="badge badge-success text-[10px]">Ranking Recorded</span>
                )}

                {connectionStatus === "disconnected" && (
                  <span className="badge badge-danger text-[10px]">Offline</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowItemsPanel(!showItemsPanel)}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs border transition-all flex items-center gap-1.5 ${
                showItemsPanel 
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200' 
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span>Items Panel</span>
            </button>

            <button
              onClick={() => {
                unlockAudio(); // gesture: enable audio output
                setVoiceOn((prev) => {
                  const next = !prev;
                  if (!next) stopAndClearVoice(); // turning off: stop now + clear queue
                  return next;
                });
              }}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs border transition-all flex items-center gap-1.5 ${
                voiceOn
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
              title={voiceOn ? "Voice on — moderator read aloud" : "Voice off"}
              aria-pressed={voiceOn}
            >
              {voiceOn ? <MdVolumeUp size={16} /> : <MdVolumeOff size={16} />}
              <span>Voice {voiceOn ? 'On' : 'Off'}</span>
            </button>

            {/* Stop the moderator's current speech (without turning voice off). Only
                shown while it's actually speaking. */}
            {isSpeaking && (
              <button
                onClick={stopAndClearVoice}
                className="px-3 py-1.5 rounded-xl font-bold text-xs border bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100 transition-all flex items-center gap-1.5"
                title="Stop the moderator's current speech"
              >
                <span>⏹ Stop</span>
              </button>
            )}

            <button
              onClick={() => setShowParticipants(!showParticipants)}
              className={`p-2 rounded-xl border transition-all ${
                showParticipants
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-white text-slate-650 border-slate-200 hover:bg-slate-50'
              }`}
              title="Participants drawer"
            >
              <MdPerson size={18} />
            </button>

            <button
              onClick={endSession}
              disabled={isLoadingFeedback}
              className="px-3.5 py-2 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 hover:text-rose-700 rounded-xl font-bold text-xs flex items-center gap-1.5 transition-all duration-200 disabled:opacity-50"
            >
              <MdExitToApp size={14} />
              <span>Leave Room</span>
            </button>
          </div>
        </div>
      </div>

      {/* 📱 WORKSPACE WRAPPER */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* 🏜️ LEFT DRAWER: Desert items references */}
        <aside
          className={`fixed md:static left-0 top-16 bottom-0 w-80 max-w-[85vw] bg-white border-r border-slate-200 shadow-xl md:shadow-none z-40 flex flex-col transition-all duration-300 ${
            showItemsPanel ? "translate-x-0 opacity-100" : "-translate-x-full md:-ml-80 opacity-0"
          }`}
        >
          <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Desert Survival Reference</h3>
              <p className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase mt-0.5">Rank Importance (1 to 12)</p>
            </div>
            <button
              type="button"
              onClick={() => setShowItemsPanel(false)}
              className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-lg text-lg leading-none"
              aria-label="Hide items panel"
            >
              ×
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
            {desertItems.map((item, idx) => (
              <div 
                key={`${idx}-${item}`} 
                className="p-3 bg-slate-50 border border-slate-200/60 rounded-xl text-xs text-slate-800 font-medium hover:border-indigo-150 hover:bg-white transition-all duration-200 shadow-[0_2px_8px_rgba(0,0,0,0.01)] flex items-start gap-2.5 group"
              >
                <span className="w-5 h-5 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center font-bold text-indigo-600 text-[10px] flex-shrink-0 group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-250">
                  {idx + 1}
                </span>
                <span className="leading-relaxed">{item}</span>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-slate-100 bg-amber-50/30">
            <h4 className="text-[11px] font-bold text-amber-800 mb-1">💬 Consensus Agreement:</h4>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              Agree out loud on your full order, from <span className="font-mono bg-amber-50/80 px-1 border border-amber-100 text-amber-900 rounded font-bold">1 (most important)</span> through <span className="font-mono bg-amber-50/80 px-1 border border-amber-100 text-amber-900 rounded font-bold">12 (least)</span>. The moderator listens to your discussion and records the group's final ranking.
            </p>
          </div>
        </aside>

        {/* 💬 MAIN CHAT SCREEN */}
        <div className="flex-1 flex flex-col overflow-hidden min-w-0 bg-white">
          
          {/* Scrollable messages log */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 select-text">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center p-4">
                <div className="text-center max-w-md animate-slide-up">
                  <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center mx-auto mb-5 text-indigo-500">
                    <MdChat className="text-3xl" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800 tracking-tight mb-2.5">
                    Desert Survival Workspace
                  </h2>
                  <p className="text-xs text-slate-500 leading-relaxed mb-6 font-medium">
                    Talk with your teammates to rank the 12 items. Work collaboratively to reach consensus under AI moderation.
                  </p>

                  <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl text-[11px] text-slate-650 leading-relaxed font-semibold max-w-sm mx-auto">
                    ⚠️ You have <strong className="text-indigo-650">15 minutes</strong> to finish. Talk through your ranking — the moderator follows the discussion and records your group's final order.
                  </div>
                </div>
              </div>
            ) : (
              messages.map((msg, index) => {
                const isModerator = msg.sender === "Moderator";
                const isSystem = msg.sender === "System";
                // 🎙️ Moderator is VOICE-ONLY: hide its conversational text from the chat
                // (participants only HEAR it). The task-intro CARD is the one exception —
                // it's the 12-item reference participants must read. TTS is unaffected
                // (it's triggered in the socket handler, not here).
                const isTaskCard =
                  msg.message_type === "task" ||
                  msg.content_format === "html" ||
                  (typeof msg.message === "string" && msg.message.includes('class="task-intro"'));
                if (isModerator && !isTaskCard) return null;
                const isFlagged = Boolean(msg.flagged);
                const isCurrentUser = msg.sender === userName;
                const userColor = !isModerator && !isSystem ? getUserColor(msg.sender, userName) : null;
                const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                }) : '';

                return (
                  <div
                    key={msg.id || `${msg.sender}-${index}-${String(msg.message).slice(0, 24)}`}
                    className={`flex items-start gap-3.5 ${isCurrentUser ? 'flex-row-reverse animate-slide-up' : 'animate-slide-up'}`}
                  >
                    {/* Avatars */}
                    <div className="flex-shrink-0">
                      {isModerator ? (
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-400 to-orange-500 flex items-center justify-center text-white shadow-md shadow-orange-100 animate-pulse-glow">
                          <span className="text-lg">🤖</span>
                        </div>
                      ) : isSystem ? (
                        <div className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-250 flex items-center justify-center text-slate-600">
                          <MdCheckCircle size={18} />
                        </div>
                      ) : (
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-extrabold shadow-sm ${userColor?.accent || 'bg-slate-500'}`}>
                          {msg.sender.charAt(0).toUpperCase()}
                        </div>
                      )}
                    </div>
                    
                    {/* Message detail container */}
                    <div className={`max-w-[75%] md:max-w-[65%] ${isCurrentUser ? 'text-right' : 'text-left'}`}>
                      <div className="flex items-center gap-2 mb-1.5 px-1">
                        <span className={`font-bold text-xs ${
                          isModerator ? 'text-amber-705' : 
                          isSystem ? 'text-slate-500' :
                          userColor?.text || 'text-slate-700'
                        }`}>
                          {isCurrentUser ? 'You' : msg.sender}
                        </span>
                        
                        <span className="text-[10px] text-slate-400 font-medium">{timestamp}</span>
                        
                        {isFlagged && !isModerator && !isSystem && (
                          <span className="badge badge-warning text-[9px] py-0 px-1.5 flex items-center gap-0.5">
                            <MdWarning size={10} />
                            Flagged
                          </span>
                        )}
                      </div>
                      
                      {/* Message Body Card */}
                      <div
                        className={`rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm border ${
                          isModerator
                            ? 'bg-amber-50/70 border-amber-200/80 text-amber-950 rounded-tl-none font-medium'
                            : isSystem
                            ? 'bg-slate-50 border-slate-200 text-slate-550 rounded-2xl text-center italic font-medium'
                            : isCurrentUser
                            ? 'bg-gradient-to-tr from-indigo-500 via-indigo-600 to-violet-650 border-indigo-650 text-white rounded-tr-none font-medium shadow-md shadow-indigo-50'
                            : `${userColor?.bg || 'bg-slate-50'} border ${userColor?.border || 'border-slate-150'} text-slate-800 rounded-tl-none font-medium`
                        } ${isFlagged && !isModerator && !isSystem ? 'ring-2 ring-amber-400 border-amber-300 bg-amber-50/40' : ''}`}
                      >
                        {isFlagged && !isModerator && !isSystem && (
                          <div
                            className={`text-[10px] font-bold mb-1.5 flex items-center gap-1.5 ${
                              isCurrentUser ? "text-amber-100" : "text-amber-900"
                            }`}
                          >
                            <MdWarning size={12} />
                            <span>This post is undergoing automated AI safety review</span>
                          </div>
                        )}
                        <ChatMessageBody msg={msg} isCurrentUser={isCurrentUser} onPlayVoice={playVoiceMessage} onSpeak={playModeratorMessage} />
                      </div>
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 🎙️ PUSH-TO-TALK CONTROL (primary input; transcript above stays read-only) */}
          <div className="border-t border-slate-200 bg-slate-50/80 backdrop-blur-md p-4">
            <div className="max-w-4xl mx-auto flex flex-col items-center gap-3">

              {/* Status indicator: Idle / Listening / Thinking / Speaking */}
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    isRecording
                      ? 'bg-rose-500 animate-pulse'
                      : sttBusy
                      ? 'bg-amber-500 animate-pulse'
                      : isSpeaking
                      ? 'bg-indigo-500 animate-pulse'
                      : 'bg-slate-300'
                  }`}
                />
                <span
                  className={
                    isRecording
                      ? 'text-rose-600'
                      : sttBusy
                      ? 'text-amber-600'
                      : isSpeaking
                      ? 'text-indigo-600'
                      : 'text-slate-400'
                  }
                >
                  {sessionStatus}
                </span>
              </div>

              {/* Big press-and-hold mic button */}
              <button
                type="button"
                onPointerDown={handlePttDown}
                onPointerUp={handlePttUp}
                onPointerCancel={handlePttUp}
                onContextMenu={(e) => e.preventDefault()}
                disabled={!ready || sttBusy}
                style={{ touchAction: "none" }}
                className={`relative w-20 h-20 rounded-full flex items-center justify-center text-white shadow-lg transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed select-none ${
                  isRecording
                    ? 'bg-rose-500 scale-105 shadow-rose-200'
                    : 'bg-gradient-to-tr from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 shadow-indigo-200'
                }`}
                aria-pressed={isRecording}
                aria-label="Press and hold to talk"
                title={ready ? "Press and hold to talk" : "Connecting…"}
              >
                {isRecording && (
                  <span className="absolute inset-0 rounded-full bg-rose-400/40 animate-ping" />
                )}
                {sttBusy ? (
                  <span className="block w-7 h-7 border-[3px] border-white/70 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <MdMic size={32} />
                )}
              </button>

              <p className="text-[11px] font-semibold text-slate-500">
                {!ready
                  ? "Connecting to room workspace…"
                  : isRecording
                  ? "Listening… release to send"
                  : sttBusy
                  ? "Transcribing your turn…"
                  : isSpeaking
                  ? "Moderator is speaking…"
                  : "Press and hold to talk"}
              </p>

              {/* Footer: role + end session (actions unchanged) */}
              <div className="w-full mt-1 px-1.5 flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span>
                  {ready ? (
                    <>Role: <span className="text-indigo-600 font-extrabold">{userName}</span></>
                  ) : (
                    <span className="text-amber-500">Connecting network...</span>
                  )}
                </span>

                <button
                  onClick={endSession}
                  disabled={isLoadingFeedback}
                  className="text-rose-500 hover:text-rose-700 flex items-center gap-1 font-bold cursor-pointer"
                >
                  {isLoadingFeedback ? (
                    <>
                      <div className="w-2.5 h-2.5 border-2 border-rose-500 border-t-transparent rounded-full animate-spin"></div>
                      <span>Analyzing feedback...</span>
                    </>
                  ) : (
                    <>
                      <MdExitToApp size={12} />
                      <span>End & Evaluate</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 👥 RIGHT DRAWER: Room Participants */}
        {showParticipants && (
          <aside className="fixed md:static right-0 top-16 bottom-0 w-80 max-w-[85vw] bg-white border-l border-slate-200 shadow-xl md:shadow-none z-40 flex flex-col animate-fade-in">
            <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-800 text-sm">Active Session Users</h3>
                <p className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase mt-0.5">Participants ({onlineCount}/3)</p>
              </div>
              <button
                type="button"
                onClick={() => setShowParticipants(false)}
                className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-lg text-base font-bold"
              >
                ×
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {/* Current user badge */}
              <div className="flex items-center gap-3 p-3 rounded-2xl bg-indigo-50/50 border border-indigo-100/60 shadow-[0_2px_8px_rgba(99,102,241,0.02)]">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-indigo-600 flex items-center justify-center text-white font-extrabold text-xs shadow-sm">
                  {userName.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-xs text-slate-800 truncate flex items-center gap-1.5">
                    <span>{userName}</span>
                    <span className="badge badge-indigo text-[8px] py-0 px-1 font-bold">You</span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-semibold flex items-center gap-1 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    Active
                  </div>
                </div>
              </div>

              {/* Teammates list */}
              {participants
                .filter(p => p !== userName)
                .map((participant, index) => {
                  const color = getUserColor(participant, userName);
                  return (
                    <div 
                      key={index} 
                      className="flex items-center gap-3 p-3 rounded-2xl border border-slate-150 hover:bg-slate-50/40 transition-all duration-200"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white font-extrabold text-xs ${color.accent}`}>
                        {participant.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-bold text-xs text-slate-850 truncate">{participant}</div>
                        <div className="text-[10px] text-slate-400 font-semibold flex items-center gap-1 mt-0.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          Online
                        </div>
                      </div>
                    </div>
                  );
                })}
              
              {/* Waiting status notifications */}
              {participants.length < 3 && (
                <div className="text-center py-6 px-4 bg-slate-50 border border-dashed border-slate-200 rounded-2xl text-[10px] text-slate-450 font-bold tracking-wide uppercase space-y-2">
                  <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p>Awaiting {3 - participants.length} more student(s)</p>
                </div>
              )}
            </div>
            
            <div className="p-4 border-t border-slate-100 bg-slate-50/40 space-y-3">
              <div className="text-[10px] text-slate-400 font-bold tracking-wide uppercase">Workspace Metadata</div>
              <div className="text-[11px] text-slate-600 font-semibold space-y-2">
                <div className="flex justify-between">
                  <span>Room ID:</span>
                  <span className="font-mono text-slate-800">{roomId.substring(0, 8)}...</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Messages:</span>
                  <span className="text-slate-800">{messages.length}</span>
                </div>
                <div className="flex justify-between">
                  <span>Subject Focus:</span>
                  <span className="text-indigo-600 uppercase text-[9px] bg-indigo-50 border border-indigo-100/60 rounded px-1 py-0.5">Desert survival</span>
                </div>
              </div>
            </div>
          </aside>
        )}
      </div>

    </div>
  );
}