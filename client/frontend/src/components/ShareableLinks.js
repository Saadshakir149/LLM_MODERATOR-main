import React, { useState } from 'react';
import { MdContentCopy, MdCheckCircle, MdPsychology, MdAutoMode } from 'react-icons/md';

export default function ShareableLinks() {
  const [copiedActive, setCopiedActive] = useState(false);
  const [copiedPassive, setCopiedPassive] = useState(false);

  const baseUrl = window.location.origin;
  const activeLink = `${baseUrl}/join/active`;
  const passiveLink = `${baseUrl}/join/passive`;

  const copyToClipboard = async (text, setterFunc) => {
    try {
      await navigator.clipboard.writeText(text);
      setterFunc(true);
      setTimeout(() => setterFunc(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      alert('Failed to copy link');
    }
  };

  return (
    <div className="glass-card p-6 md:p-8 animate-slide-up">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-800 tracking-tight mb-2">
          Quick Join Links
        </h2>
        <p className="text-sm text-slate-500 max-w-sm mx-auto">
          Distribute these direct entry points to students for instant session participation
        </p>
      </div>

      <div className="space-y-6">
        {/* Active Mode Link */}
        <div className="bg-white/50 border border-slate-100 rounded-2xl p-5 hover:border-indigo-200 hover:shadow-md transition-all duration-300 group">
          <div className="flex items-center mb-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 mr-3 group-hover:scale-110 transition-transform">
              <MdPsychology className="text-2xl" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-base leading-tight">
                Active Moderation Mode
              </h3>
              <p className="text-xs text-slate-500">
                AI facilitates and adaptive-guides the narrative progress
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 mt-4">
            <input
              type="text"
              value={activeLink}
              readOnly
              className="flex-1 px-3 py-2.5 bg-slate-50/80 border border-slate-200 rounded-xl text-xs font-mono text-indigo-700 outline-none"
            />
            <button
              onClick={() => copyToClipboard(activeLink, setCopiedActive)}
              className={`px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all duration-200 ${
                copiedActive 
                  ? 'bg-emerald-500 text-white shadow-md shadow-emerald-100' 
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm'
              }`}
            >
              {copiedActive ? (
                <>
                  <MdCheckCircle className="text-base" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <MdContentCopy className="text-base" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Passive Mode Link */}
        <div className="bg-white/50 border border-slate-100 rounded-2xl p-5 hover:border-purple-200 hover:shadow-md transition-all duration-300 group">
          <div className="flex items-center mb-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600 mr-3 group-hover:scale-110 transition-transform">
              <MdAutoMode className="text-2xl" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-base leading-tight">
                Passive Progress Mode
              </h3>
              <p className="text-xs text-slate-500">
                AI observes and the story advances automatically
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 mt-4">
            <input
              type="text"
              value={passiveLink}
              readOnly
              className="flex-1 px-3 py-2.5 bg-slate-50/80 border border-slate-200 rounded-xl text-xs font-mono text-purple-700 outline-none"
            />
            <button
              onClick={() => copyToClipboard(passiveLink, setCopiedPassive)}
              className={`px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all duration-200 ${
                copiedPassive 
                  ? 'bg-emerald-500 text-white shadow-md shadow-emerald-100' 
                  : 'bg-purple-600 hover:bg-purple-700 text-white shadow-sm'
              }`}
            >
              {copiedPassive ? (
                <>
                  <MdCheckCircle className="text-base" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <MdContentCopy className="text-base" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="mt-8 p-4 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 rounded-2xl border border-indigo-50/50">
        <h4 className="font-bold text-indigo-900 text-xs tracking-wide uppercase mb-2">📋 Instructions:</h4>
        <ul className="text-xs text-indigo-750/90 space-y-1.5 leading-relaxed">
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
            Send links directly to students via chat or email.
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
            Supports up to 3 collaborative users per room session.
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
            System dynamically creates new overflow rooms when active ones fill up.
          </li>
        </ul>
      </div>
    </div>
  );
}
