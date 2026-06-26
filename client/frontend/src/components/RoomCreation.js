// ============================================================
// path: src/components/RoomCreation.jsx
// COMPLETELY FIXED VERSION - Join Room Button Working, No Page Refresh
// ============================================================

import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { socket } from "../socket";
import ShareableLinks from "./ShareableLinks";
import {
  MdPerson,
  MdMeetingRoom,
  MdPlayArrow,
  MdLogin,
  MdPsychology,
  MdSchool,
  MdGroups,
  MdAutoAwesome
} from "react-icons/md";

export default function RoomCreation() {
  const [activeTab, setActiveTab] = useState("create");
  const [roomId, setRoomId] = useState("");
  const [userName, setUserName] = useState("");
  const [major, setMajor] = useState("computer_science");
  const [activeModerator, setActiveModerator] = useState(true);
  const [loading, setLoading] = useState(false);
  const mountedRef = useRef(true);
  const navigate = useNavigate();

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // ============================================================
  // ✅ FIXED: Create Room Function
  // ============================================================
  const createRoom = () => {
    const name = userName.trim();
    if (!name) {
      alert("Please enter your name first.");
      return;
    }

    setLoading(true);
    console.log("Creating room for:", name);

    let connectTimeoutId = null;

    const cleanup = () => {
      if (connectTimeoutId) {
        clearTimeout(connectTimeoutId);
        connectTimeoutId = null;
      }
    };

    const onRoomCreated = (data) => {
      cleanup();
      socket.off("error", onError);
      console.log("Room created:", data);
      if (!mountedRef.current) return;
      setLoading(false);
      navigate(
        `/chat/${data.room_id}?userName=${encodeURIComponent(name)}&major=${major}&activeModerator=${activeModerator}`
      );
    };

    const onError = (error) => {
      cleanup();
      socket.off("room_created", onRoomCreated);
      console.error("Room creation error:", error);
      if (!mountedRef.current) return;
      setLoading(false);
      const msg =
        typeof error === "string"
          ? error
          : error?.message || "Failed to create room. Please try again.";
      alert(msg);
    };

    // Register handlers BEFORE emit — otherwise a fast server response can be missed.
    socket.once("room_created", onRoomCreated);
    socket.once("error", onError);

    const emitCreateRoom = () => {
      console.log("Emitting create_room event");
      socket.emit("create_room", {
        user_name: name,
        major: major,
        moderatorMode: activeModerator ? "active" : "passive",
      });
    };

    if (socket.connected) {
      emitCreateRoom();
    } else {
      console.log("Socket not connected, connecting now...");
      socket.connect();
      socket.once("connect", () => {
        console.log("Socket connected, now emitting");
        emitCreateRoom();
      });
      connectTimeoutId = setTimeout(() => {
        if (!socket.connected) {
          socket.off("room_created", onRoomCreated);
          socket.off("error", onError);
          if (mountedRef.current) {
            setLoading(false);
            alert("Connection timeout. Please check your internet and try again.");
          }
        }
      }, 15000);
    }
  };

  // ============================================================
  // ✅ FIXED: Join Room Function - No Page Refresh, Proper Loading
  // ============================================================
  const joinRoom = (e) => {
    if (e) e.preventDefault();
    if (loading) return;

    const name = userName.trim();
    const id = roomId.trim();

    if (!name) {
      alert("Please enter your name first.");
      return;
    }
    if (!id) {
      alert("Please enter a Room ID.");
      return;
    }

    setLoading(true);
    navigate(
      `/chat/${encodeURIComponent(id)}?userName=${encodeURIComponent(name)}&major=${major}&activeModerator=${activeModerator}`
    );
  };

  return (
    <div className="min-h-screen gradient-bg py-10 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <div className="text-center mb-12 animate-slide-up">
          <div className="flex items-center justify-center gap-3.5 mb-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 via-indigo-650 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-150 animate-pulse-glow">
              <MdAutoAwesome className="text-3xl text-white" />
            </div>
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-600 via-indigo-800 to-violet-700 bg-clip-text text-transparent">
              LLM Moderator
            </h1>
          </div>
          <p className="text-base md:text-lg text-slate-650 max-w-xl mx-auto font-medium">
            AI-moderated collaborative educational environments. Create sessions, share links, or join rooms instantly.
          </p>
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-2 gap-8 items-start">
          {/* Left: Info/Shareable Links */}
          <div className="space-y-8 animate-slide-up [animation-delay:100ms]">
            <ShareableLinks />
            
            {/* Stats/Info Card */}
            <div className="glass-card p-6 md:p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-650">
                  <MdGroups className="text-2xl" />
                </div>
                <h3 className="text-xl font-bold text-slate-800">How It Works</h3>
              </div>
              <div className="relative border-l border-slate-100 pl-6 ml-5 space-y-8">
                <div className="relative">
                  <span className="absolute -left-11 top-0 w-8 h-8 rounded-full bg-indigo-50 border-2 border-white flex items-center justify-center text-xs font-bold text-indigo-600 shadow-sm">
                    1
                  </span>
                  <div>
                    <h4 className="font-bold text-slate-800 text-sm mb-1">Select Moderation Mode</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      Choose <strong>Active</strong> for real-time AI prompts and hints, or <strong>Passive</strong> for self-directed discussions.
                    </p>
                  </div>
                </div>
                
                <div className="relative">
                  <span className="absolute -left-11 top-0 w-8 h-8 rounded-full bg-indigo-50 border-2 border-white flex items-center justify-center text-xs font-bold text-indigo-600 shadow-sm">
                    2
                  </span>
                  <div>
                    <h4 className="font-bold text-slate-800 text-sm mb-1">Invite Participants</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      Share room IDs or distribute direct link invites to form groups of up to three students.
                    </p>
                  </div>
                </div>

                <div className="relative">
                  <span className="absolute -left-11 top-0 w-8 h-8 rounded-full bg-indigo-50 border-2 border-white flex items-center justify-center text-xs font-bold text-indigo-600 shadow-sm">
                    3
                  </span>
                  <div>
                    <h4 className="font-bold text-slate-800 text-sm mb-1">Collaborative Narrative</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      Solve tasks or discuss stories. The AI moderator dynamically adjusts interaction based on student contributions.
                    </p>
                  </div>
                </div>

                <div className="relative">
                  <span className="absolute -left-11 top-0 w-8 h-8 rounded-full bg-indigo-50 border-2 border-white flex items-center justify-center text-xs font-bold text-indigo-600 shadow-sm">
                    4
                  </span>
                  <div>
                    <h4 className="font-bold text-slate-800 text-sm mb-1">Receive Analytical Feedback</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      Get automated, personalized feedback detailing strengths and academic developmental suggestions.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Create/Join Form */}
          <div className="glass-card p-6 md:p-8 shadow-2xl border border-white/50 animate-slide-up [animation-delay:200ms]">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-slate-800 mb-2">Room Setup Portal</h2>
              <p className="text-sm text-slate-500">Initialize a new session or join an ongoing workspace</p>
            </div>

            <div className="space-y-6">
              {/* User Info */}
              <div>
                <label className="block text-xs font-bold text-slate-650 uppercase tracking-wider mb-2">
                  <div className="flex items-center gap-2">
                    <MdPerson className="text-slate-400 text-base" />
                    <span>Your Display Name</span>
                  </div>
                </label>
                <input
                  type="text"
                  placeholder="Enter your name"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="input-field shadow-sm"
                  disabled={loading}
                />
              </div>

              {/* Tab Selector */}
              <div className="flex border border-slate-100/80 mb-6 bg-slate-50/50 p-1.5 rounded-2xl">
                <button
                  type="button"
                  onClick={() => setActiveTab("create")}
                  className={`flex-1 py-3 rounded-xl text-xs font-bold transition-all duration-300 ${
                    activeTab === "create"
                      ? "bg-white text-indigo-600 shadow-sm border border-slate-100"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  Create Session
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("join")}
                  className={`flex-1 py-3 rounded-xl text-xs font-bold transition-all duration-300 ${
                    activeTab === "join"
                      ? "bg-white text-indigo-600 shadow-sm border border-slate-100"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  Join Session
                </button>
              </div>

              {activeTab === "create" ? (
                /* CREATE TAB */
                <div className="space-y-6 animate-fade-in">
                  {/* Major Selection */}
                  <div>
                    <label className="block text-xs font-bold text-slate-650 uppercase tracking-wider mb-2">
                      <div className="flex items-center gap-2">
                        <MdSchool className="text-slate-400 text-base" />
                        <span>Academic Major</span>
                      </div>
                    </label>
                    <select
                      value={major}
                      onChange={(e) => setMajor(e.target.value)}
                      className="select-field shadow-sm"
                      disabled={loading}
                    >
                      <optgroup label="STEM">
                        <option value="computer_science">Computer Science</option>
                        <option value="data_science">Data Science</option>
                        <option value="engineering">Engineering</option>
                        <option value="mathematics">Mathematics</option>
                      </optgroup>
                      <optgroup label="Humanities">
                        <option value="education">Education</option>
                        <option value="psychology">Psychology</option>
                        <option value="sociology">Sociology</option>
                      </optgroup>
                      <optgroup label="Business">
                        <option value="business">Business</option>
                        <option value="economics">Economics</option>
                      </optgroup>
                      <optgroup label="Creative">
                        <option value="media">Media</option>
                        <option value="design">Design</option>
                        <option value="architecture">Architecture</option>
                      </optgroup>
                      <optgroup label="Health">
                        <option value="nursing">Nursing</option>
                        <option value="health_science">Health Science</option>
                      </optgroup>
                    </select>
                  </div>

                  {/* Moderator Toggle */}
                  <div className="p-4 bg-gradient-to-r from-indigo-50/50 to-purple-50/50 border border-indigo-50/80 rounded-2xl shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-indigo-650 shadow-sm">
                          <MdPsychology className="text-xl" />
                        </div>
                        <div>
                          <h4 className="font-bold text-sm text-slate-800">AI Moderation</h4>
                          <p className="text-xs text-slate-500 font-semibold">
                            {activeModerator ? "Active engagement mode" : "Passive observation mode"}
                          </p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={activeModerator}
                          onChange={(e) => setActiveModerator(e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-indigo-500 peer-checked:to-purple-500"></div>
                      </label>
                    </div>
                  </div>

                  {/* Create Button */}
                  <button
                    onClick={createRoom}
                    disabled={loading || !userName.trim()}
                    className="w-full btn-primary py-3.5 flex items-center justify-center gap-2 shadow-lg shadow-indigo-100"
                  >
                    <MdPlayArrow className="text-xl" />
                    <span>{loading ? "Creating Room..." : "Create New Room"}</span>
                  </button>
                </div>
              ) : (
                /* JOIN TAB */
                <div className="space-y-6 animate-fade-in">
                  <div>
                    <label className="block text-xs font-bold text-slate-650 uppercase tracking-wider mb-2">
                      <div className="flex items-center gap-2">
                        <MdMeetingRoom className="text-slate-400 text-base" />
                        <span>Room ID</span>
                      </div>
                    </label>
                    
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Paste room ID here"
                        value={roomId}
                        onChange={(e) => setRoomId(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            joinRoom(e);
                          }
                        }}
                        className="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-2xl outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100/50 transition duration-200 text-sm shadow-sm"
                        disabled={loading}
                      />
                      <button
                        onClick={(e) => joinRoom(e)}
                        disabled={loading || !userName.trim() || !roomId.trim()}
                        className="px-6 py-3 bg-slate-800 hover:bg-slate-900 text-white rounded-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 font-semibold text-sm whitespace-nowrap shadow-md shadow-slate-100"
                      >
                        <MdLogin size={16} />
                        <span>{loading ? "Joining..." : "Join"}</span>
                      </button>
                    </div>
                    
                    {/* Validation notices */}
                    {!userName.trim() && roomId.trim() && (
                      <p className="text-[11px] text-red-500 font-semibold mt-3 flex items-center gap-1.5 animate-fade-in">
                        <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                        Please input your display name first
                      </p>
                    )}
                    {userName.trim() && !roomId.trim() && (
                      <p className="text-[11px] text-slate-400 font-semibold mt-3 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
                        Paste code above to join workspace
                      </p>
                    )}
                    {userName.trim() && roomId.trim() && (
                      <p className="text-[11px] text-emerald-600 font-semibold mt-3 flex items-center gap-1.5 animate-fade-in">
                        <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                        Validating room destination: <span className="font-mono bg-emerald-50 px-1 py-0.5 rounded border border-emerald-100">
                          {roomId.length > 12 ? `${roomId.substring(0, 8)}...${roomId.substring(roomId.length - 4)}` : roomId}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}