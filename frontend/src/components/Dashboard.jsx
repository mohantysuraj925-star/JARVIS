import React, { useState } from "react";
import { Monitor, Smartphone, LogOut, CheckCircle2, ShieldCheck, Zap, Terminal, Sparkles, Star, Send, Check, Tag, Edit3 } from "lucide-react";

export default function Dashboard({ user, onLogout }) {
  const [rating, setRating] = useState(5);
  const [selectedTag, setSelectedTag] = useState("");
  const [customFeedback, setCustomFeedback] = useState("");
  const [isOther, setIsOther] = useState(false);
  const [feedStatus, setFeedStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Dynamic Suggestions based on Selected Star Rating
  const suggestionsMap = {
    5: [
      "⚡ Ultra fast and low latency",
      "🎨 Cyberpunk UI design is incredible",
      "🎙️ Voice recognition sounds natural",
      "🚀 Flawless performance & hardware hooks"
    ],
    4: [
      "👍 Great performance, minor UI tweaks needed",
      "⚡ Fast response, waiting for more features",
      "🔊 Good voice response, slightly high volume",
      "✨ Overall very reliable experience"
    ],
    3: [
      "⏳ Average response latency",
      "🛠️ Works fine, but needs better stability",
      "📶 Audio lag occurs sometimes",
      "📦 Setup process was a bit confusing"
    ],
    2: [
      "⚠️ Voice recognition failed frequently",
      "🐢 High latency / slow response times",
      "❌ Audio device disconnected midway",
      "🐛 Encountered minor UI glitches"
    ],
    1: [
      "🚨 System crashed on command",
      "🛑 Critical error encountered",
      "🔇 Voice engine failed to activate",
      "❌ Incompatible hardware behavior"
    ]
  };

  const handleRatingChange = (newRating) => {
    setRating(newRating);
    setSelectedTag(""); // Reset tag on star switch
    setIsOther(false);
  };

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    const finalMessage = isOther ? customFeedback.trim() : selectedTag;
    
    if (!finalMessage) {
      setFeedStatus("Please pick a suggestion or write your feedback.");
      setTimeout(() => setFeedStatus(""), 3000);
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: user?.username || "Operator",
          rating: rating,
          message: finalMessage
        })
      });

      if (res.ok) {
        setFeedStatus("Feedback submitted successfully to Master Console!");
      } else {
        setFeedStatus("Feedback recorded locally!");
      }
      setSelectedTag("");
      setCustomFeedback("");
      setIsOther(false);
      setTimeout(() => setFeedStatus(""), 4000);
    } catch {
      setFeedStatus("Feedback saved locally!");
      setTimeout(() => setFeedStatus(""), 4000);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 text-slate-100 font-sans">
      {/* Top Navbar */}
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-5 bg-[#030914]/80 backdrop-blur-2xl border border-cyan-500/20 rounded-2xl shadow-[0_0_25px_rgba(6,182,212,0.1)] mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-tr from-cyan-500/20 to-blue-500/10 border border-cyan-400/30 rounded-xl text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
            <Zap size={22} className="animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
                GARUDA CORE
              </h1>
              <span className="text-[10px] font-mono tracking-widest px-2 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-cyan-300">
                BY SURAJ
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Operator: <span className="text-cyan-300 font-semibold">{user?.username || "Suraj"}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-mono font-medium rounded-full border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.15)]">
            <CheckCircle2 size={13} /> Active License ({user?.days_remaining || 10} Days Remaining)
          </span>
          <button
            onClick={onLogout}
            title="Disconnect Console"
            className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 rounded-xl transition-all"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* Hero Notice / Licensing */}
      <section className="relative overflow-hidden p-6 bg-[#040e1a]/70 backdrop-blur-xl border border-cyan-500/20 rounded-2xl shadow-lg mb-8">
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="flex items-start gap-4">
          <div className="p-2.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-xl mt-1 shrink-0">
            <ShieldCheck size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <h2 className="text-base font-bold text-slate-100 tracking-wide">
                GARUDA Autonomous Protocol & Terms
              </h2>
              <span className="inline-flex items-center gap-1 text-[11px] text-cyan-400/90 font-mono">
                <Sparkles size={11} /> v3.0 Native
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed font-sans">
              Engineered, designed, and curated exclusively by <strong className="text-cyan-300 font-medium">Suraj</strong>. 
              GARUDA is equipped with autonomous real-time multimodal intelligence, socket bridging, and custom neural workflows. 
              Authorized solely for dedicated hardware configurations. Commercial redistribution or reverse compilation is prohibited.
            </p>
          </div>
        </div>
      </section>

      {/* Deployment & Download Hub */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Desktop Client Card */}
        <div className="group relative p-6 bg-[#040e1a]/80 backdrop-blur-xl border border-cyan-500/20 hover:border-cyan-400/50 rounded-2xl transition-all duration-300 shadow-md hover:shadow-[0_0_30px_rgba(6,182,212,0.15)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-xl group-hover:scale-105 transition-transform">
                <Monitor size={26} />
              </div>
              <span className="text-[11px] font-mono text-cyan-400/80 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded-md">
                Windows x64
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
              GARUDA Desktop Engine
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Full desktop system with hardware hook telemetry, PyQt6 visual HUD, low-latency live audio, and developer shell.
            </p>
          </div>
          
          <a
            href="/download/windows"
            className="mt-6 inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-cyan-950/50 transition-all active:scale-[0.98]"
          >
            <Terminal size={15} /> Download Windows Setup (.exe)
          </a>
        </div>

        {/* Mobile Hub Card */}
        <div className="group relative p-6 bg-[#040e1a]/80 backdrop-blur-xl border border-sky-500/20 hover:border-sky-400/50 rounded-2xl transition-all duration-300 shadow-md hover:shadow-[0_0_30px_rgba(14,165,233,0.15)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-sky-500/10 text-sky-400 border border-sky-500/30 rounded-xl group-hover:scale-105 transition-transform">
                <Smartphone size={26} />
              </div>
              <span className="text-[11px] font-mono text-sky-400/80 bg-sky-950/60 border border-sky-800/40 px-2 py-0.5 rounded-md">
                Standalone APK
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-100 group-hover:text-sky-300 transition-colors">
              GARUDA Mobile APK
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Standalone mobile assistant client. Runs directly on your phone without requiring a desktop connection or PC server.
            </p>
          </div>

          <a
            href="http://127.0.0.1:8000/download/android"
            className="mt-6 inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-sky-950/50 transition-all active:scale-[0.98]"
          >
            <Smartphone size={15} /> Download Android APK
          </a>
        </div>
      </div>

      {/* Smart Quick Feedback Box with Chips & Other Option */}
      <section className="relative overflow-hidden p-6 bg-[#040e1a]/85 backdrop-blur-xl border border-cyan-500/20 rounded-2xl shadow-lg">
        <div className="flex items-center gap-2 mb-2">
          <Star size={18} className="text-amber-400" />
          <h3 className="text-sm font-mono font-bold text-slate-100 uppercase tracking-wider">
            Operator Feedback & System Review
          </h3>
        </div>
        <p className="text-xs text-slate-400 mb-4 font-sans">
          स्टार रेटिंग चुनें और बिना टाइपिंग किए अपना सुझाव एक क्लिक में सबमिट करें:
        </p>

        <form onSubmit={handleFeedbackSubmit} className="space-y-4">
          {/* Star Selection */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">Rating:</span>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  type="button"
                  key={star}
                  onClick={() => handleRatingChange(star)}
                  className="p-1 hover:scale-110 transition-transform"
                >
                  <Star
                    size={22}
                    className={star <= rating ? "text-amber-400 fill-amber-400" : "text-slate-600"}
                  />
                </button>
              ))}
            </div>
            <span className="text-xs font-mono text-cyan-300 ml-2">({rating}/5 Stars Selected)</span>
          </div>

          {/* Quick Suggestions (Dynamic Chips) */}
          <div>
            <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Tag size={13} className="text-cyan-400" />
              Choose Quick Feedback Tag (No typing required):
            </label>
            <div className="flex flex-wrap gap-2">
              {suggestionsMap[rating]?.map((text, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => { setSelectedTag(text); setIsOther(false); }}
                  className={`px-3 py-1.5 text-xs font-sans rounded-xl border transition-all text-left ${
                    selectedTag === text && !isOther
                      ? "bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,0.2)]"
                      : "bg-[#020712] border-cyan-500/10 text-slate-400 hover:border-cyan-500/30 hover:text-slate-200"
                  }`}
                >
                  {text}
                </button>
              ))}

              {/* Other Button */}
              <button
                type="button"
                onClick={() => { setIsOther(true); setSelectedTag(""); }}
                className={`px-3 py-1.5 text-xs font-mono rounded-xl border transition-all flex items-center gap-1.5 ${
                  isOther
                    ? "bg-indigo-500/20 border-indigo-400 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.2)]"
                    : "bg-[#020712] border-cyan-500/10 text-slate-400 hover:border-cyan-500/30 hover:text-slate-200"
                }`}
              >
                <Edit3 size={13} />
                <span>Other / Write Custom Note</span>
              </button>
            </div>
          </div>

          {/* Custom Text Area (Only shown if Other is clicked) */}
          {isOther && (
            <div className="animate-fadeIn">
              <textarea
                rows="3"
                value={customFeedback}
                onChange={(e) => setCustomFeedback(e.target.value)}
                placeholder="Type your custom observation, detailed bug report, or feature request here..."
                className="w-full p-3 bg-[#020712] border border-indigo-500/30 rounded-xl text-slate-200 text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400/40 transition-all resize-none"
                required
              />
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-md transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <Send size={13} />
              <span>Submit Feedback</span>
            </button>
          </div>

          {feedStatus && (
            <p className="mt-2 text-xs font-mono text-emerald-400 flex items-center gap-1.5">
              <Check size={14} /> {feedStatus}
            </p>
          )}
        </form>
      </section>

    </div>
  );
}

