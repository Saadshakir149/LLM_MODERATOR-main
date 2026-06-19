// =========================
// Auto Join Component - FIXED VERSION
// Automatically assigns user to available room with socket connection check
// =========================
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { socket } from '../socket'; // 👈 IMPORT SOCKET

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function AutoJoin() {
  const { mode } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  // Participants pick their group's language BEFORE joining, so the moderator speaks
  // it from the very first turn (no waiting for an Urdu message to be detected).
  const [language, setLanguage] = useState('en');

  const joinRoom = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!socket.connected) {
        socket.connect();
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => reject(new Error("Socket connection timeout")), 5000);
          socket.once("connect", () => { clearTimeout(timeout); resolve(); });
        });
      }

      const response = await fetch(`${API_URL}/join/${mode}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to join room');

      const userName = data.user_name || `Student ${Math.floor(Math.random() * 1000)}`;
      // Carry the chosen language so ChatRoom sends it in join_room and the room pins it.
      navigate(
        `/chat/${data.room_id}?userName=${encodeURIComponent(userName)}&language=${encodeURIComponent(language)}`
      );
    } catch (err) {
      console.error('❌ AutoJoin Error:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mode !== 'active' && mode !== 'passive') {
      setError('Invalid mode. Use /join/active or /join/passive');
    }
  }, [mode]);

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-4 md:p-8">
      <div className="glass-card max-w-md w-full p-8 md:p-10 border border-white/50 shadow-2xl animate-slide-up">
        {loading ? (
          <div className="text-center">
            <div className="relative flex items-center justify-center w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-100 border-t-indigo-600 animate-spin"></div>
              <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 animate-pulse-glow">
                <span className="font-bold text-xs font-display">AI</span>
              </div>
            </div>
            
            <h2 className="text-2xl font-bold text-slate-800 tracking-tight mb-2">
              Assigning Workspace...
            </h2>
            
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 border border-indigo-100 rounded-full text-xs font-semibold text-indigo-750 mt-1">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
              </span>
              <span>{mode === 'active' ? 'Active Engagement' : 'Passive Observation'}</span>
            </div>

            <p className="text-xs text-slate-500 mt-6 leading-relaxed max-w-xs mx-auto">
              Please hold on while the server finds or constructs an available room for you.
            </p>
          </div>
        ) : error ? (
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-rose-50 flex items-center justify-center text-rose-500 mx-auto mb-6">
              <span className="text-3xl">⚠️</span>
            </div>
            
            <h2 className="text-2xl font-bold text-slate-800 tracking-tight mb-2">
              Assignment Error
            </h2>
            
            <p className="text-sm text-slate-650 mb-6 bg-rose-50/50 border border-rose-100/50 p-3 rounded-2xl">
              {error}
            </p>
            
            <button
              onClick={() => navigate('/')}
              className="btn-primary w-full shadow-md shadow-indigo-100"
            >
              Return to Setup
            </button>
          </div>
        ) : (
          <div className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 mx-auto mb-5">
              <span className="text-3xl">🎙️</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-800 tracking-tight mb-1">
              Choose your language
            </h2>
            <p className="text-xs text-slate-500 mb-6 leading-relaxed max-w-xs mx-auto">
              The moderator will speak this language for the whole session.
              <br />Aap ki pasand ki zaban chunein.
            </p>

            <div className="grid grid-cols-2 gap-3 mb-6">
              <button
                onClick={() => setLanguage('en')}
                className={`py-3 rounded-2xl border text-sm font-bold transition-all ${
                  language === 'en'
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-md'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-indigo-300'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage('roman_urdu')}
                className={`py-3 rounded-2xl border text-sm font-bold transition-all ${
                  language === 'roman_urdu'
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-md'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-indigo-300'
                }`}
              >
                Roman Urdu
              </button>
            </div>

            <button onClick={joinRoom} className="btn-primary w-full shadow-md shadow-indigo-100">
              Join {mode === 'active' ? 'Active' : 'Passive'} Session
            </button>
          </div>
        )}
      </div>
    </div>
  );
}