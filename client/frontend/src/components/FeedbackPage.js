// =========================
// FeedbackPage.js - MINIMALIST PROFESSIONAL DESIGN
// =========================
import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import rehypeSanitize from "rehype-sanitize";
import { MdArrowBack, MdDownload, MdShare, MdStar } from "react-icons/md";

const FEEDBACK_MARKDOWN_COMPONENTS = {
  p: ({ children, ...rest }) => (
    <p className="mb-3 last:mb-0 text-gray-700 leading-relaxed" {...rest}>
      {children}
    </p>
  ),
  strong: ({ children, ...rest }) => (
    <strong className="font-semibold text-gray-900" {...rest}>
      {children}
    </strong>
  ),
  em: ({ children, ...rest }) => (
    <em className="italic text-gray-700" {...rest}>
      {children}
    </em>
  ),
  ul: ({ children, ...rest }) => (
    <ul className="list-disc pl-5 space-y-1 mb-3 text-gray-700" {...rest}>
      {children}
    </ul>
  ),
  ol: ({ children, ...rest }) => (
    <ol className="list-decimal pl-5 space-y-1 mb-3 text-gray-700" {...rest}>
      {children}
    </ol>
  ),
  li: ({ children, ...rest }) => (
    <li className="leading-relaxed" {...rest}>
      {children}
    </li>
  ),
  h1: ({ children, ...rest }) => (
    <h1 className="text-xl font-bold text-gray-900 mt-2 mb-3" {...rest}>
      {children}
    </h1>
  ),
  h2: ({ children, ...rest }) => (
    <h2 className="text-lg font-semibold text-gray-900 mt-4 mb-2" {...rest}>
      {children}
    </h2>
  ),
  h3: ({ children, ...rest }) => (
    <h3 className="text-base font-semibold text-indigo-800 mt-3 mb-2" {...rest}>
      {children}
    </h3>
  ),
};

function deriveNameFromGreeting(text) {
  if (!text || typeof text !== "string") return "";
  const m = text.match(/Hi\s+([^,]+),/i);
  return m ? m[1].trim() : "";
}

export default function FeedbackPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(true);
  const [studentName, setStudentName] = useState("");

  useEffect(() => {
    const stateFeedback = location.state?.feedback;
    const fromNavName = (location.state?.studentName || "").trim();
    const targetUser = (location.state?.targetUsername || "").trim();

    if (stateFeedback) {
      setFeedback(stateFeedback);
      setStudentName(
        fromNavName || targetUser || deriveNameFromGreeting(stateFeedback)
      );
      setLoading(false);
      return;
    }

    const savedFeedback = localStorage.getItem("lastFeedback");
    if (savedFeedback) {
      setFeedback(savedFeedback);
      setStudentName(deriveNameFromGreeting(savedFeedback));
    }
    setLoading(false);
  }, [location.state]);

  const downloadFeedback = () => {
    const element = document.createElement("a");
    const file = new Blob([feedback], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = `feedback-${studentName || "session"}-${new Date().toISOString().split("T")[0]}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const shareFeedback = () => {
    if (navigator.share) {
      navigator
        .share({
          title: `Feedback for ${studentName || "Session"}`,
          text: feedback,
        })
        .catch(() => copyToClipboard());
    } else {
      copyToClipboard();
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(feedback);
    alert("✅ Feedback copied to clipboard");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading feedback...</p>
        </div>
      </div>
    );
  }  return (
    <div className="min-h-screen gradient-bg py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-slate-500 hover:text-indigo-650 mb-8 transition-colors duration-200 group font-semibold text-sm cursor-pointer"
        >
          <MdArrowBack className="group-hover:-translate-x-1.5 transition-transform text-lg" />
          <span>Back to Dashboard</span>
        </button>

        <div className="glass-card overflow-hidden shadow-xl border border-white/50 animate-slide-up">
          <div className="px-6 py-6 md:px-8 border-b border-slate-100 bg-white/40">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800 tracking-tight">Session Assessment</h1>
                <p className="text-xs text-indigo-600 font-semibold uppercase tracking-wider mt-1">
                  {studentName ? `Feedback report for ${studentName}` : "Personalized learning assessment"}
                </p>
              </div>
              <div className="flex items-center gap-1.5 bg-yellow-50 border border-yellow-100 px-3 py-1.5 rounded-2xl animate-pulse-glow w-fit">
                {[1, 2, 3, 4, 5].map((star) => (
                  <MdStar key={star} className="w-5 h-5 text-yellow-500" />
                ))}
              </div>
            </div>
          </div>

          <div className="px-6 py-6 md:px-8 feedback-content max-w-none text-slate-700 bg-white/70">
            {feedback ? (
              <div className="prose prose-indigo max-w-none text-sm leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkBreaks]}
                  rehypePlugins={[rehypeSanitize]}
                  components={FEEDBACK_MARKDOWN_COMPONENTS}
                >
                  {feedback}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-slate-500 text-center py-6">No evaluation notes are logged for this room session.</p>
            )}
          </div>

          <div className="px-6 py-5 md:px-8 bg-slate-50/50 border-t border-slate-150 flex justify-end gap-3.5">
            <button
              onClick={downloadFeedback}
              disabled={!feedback}
              className="btn-secondary py-2.5 px-4 flex items-center gap-2"
            >
              <MdDownload className="text-base" />
              <span>Download TXT</span>
            </button>
            <button
              onClick={shareFeedback}
              disabled={!feedback}
              className="btn-primary py-2.5 px-4 flex items-center gap-2 shadow-sm"
            >
              <MdShare className="text-base" />
              <span>Share Report</span>
            </button>
          </div>
        </div>

        <div className="mt-6 glass-card p-4 md:p-5 border border-white/50">
          <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider">
            <span>Session Status</span>
            <span className="text-indigo-600 bg-indigo-50 border border-indigo-100 rounded px-2 py-0.5">
              Completed on {new Date().toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
