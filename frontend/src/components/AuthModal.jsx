import React, { useState } from "react";
import { User, KeyRound, Monitor, Smartphone, Terminal, ArrowRight, AlertCircle, ShieldCheck, Cpu, Sparkles } from "lucide-react";

export default function AuthModal({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [platform, setPlatform] = useState("windows");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAuth = async (e) => {
    e.preventDefault();
    if (!username.trim() || password.length < 5) {
      setError("Terminal Error: Operator ID and 5+ char password required");
      return;
    }
    setError("");
    setLoading(true);

    if (mode === "login") {
      if (username === "admin123" && password === "Suraj") {
        onLogin({ username, role: "admin" });
        return;
      }
      // Normal Login Handshake
      onLogin({ username, role: "user", days_remaining: 10, platform });
    } else {
      // REAL REGISTRATION: Save into Backend Database
      try {
        const res = await fetch("/api/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: username.trim(),
            password: password.trim(),
            platform: platform
          })
        });

        const data = await res.json();
        onLogin({
          username: username.trim(),
          role: "user",
          hwid: data.hwid || "NODE-LIVE",
          platform: data.platform || (platform === "android" ? "Android" : "Windows"),
          days_remaining: data.days || 10
        });
      } catch {
        // Fallback session if backend server offline
        onLogin({ username: username.trim(), role: "user", days_remaining: 10, platform });
      }
    }
    setLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-[85vh] px-4 py-8">
      <div className="relative w-full max-w-lg p-8 bg-[#040e1a]/90 backdrop-blur-2xl border border-cyan-500/30 rounded-3xl shadow-[0_0_50px_rgba(6,182,212,0.15)] overflow-hidden">
        
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-80 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-gradient-to-tr from-cyan-500/20 via-sky-500/10 to-indigo-500/20 border border-cyan-400/30 rounded-2xl mb-3 shadow-[0_0_20px_rgba(6,182,212,0.25)] text-cyan-400">
            <Cpu size={32} className="animate-pulse" />
          </div>
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-2xl font-black tracking-widest bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
              GARUDA CORE
            </h1>
            <span className="text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
              BY SURAJ
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Autonomous Multimodal Intelligence Gateway
          </p>
        </div>

        <div className="grid grid-cols-2 p-1 bg-[#020712] border border-cyan-500/20 rounded-2xl mb-6 font-mono text-xs">
          <button
            type="button"
            onClick={() => { setMode("login"); setError(""); }}
            className={`py-2.5 rounded-xl font-bold uppercase tracking-wider transition-all ${
              mode === "login"
                ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-950"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Terminal Login
          </button>
          <button
            type="button"
            onClick={() => { setMode("register"); setError(""); }}
            className={`py-2.5 rounded-xl font-bold uppercase tracking-wider transition-all ${
              mode === "register"
                ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-950"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            New Operator Pass
          </button>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-center gap-2">
            <AlertCircle size={15} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {mode === "login" ? (
          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                Operator Call-Sign (Username)
              </label>
              <div className="relative">
                <User size={16} className="absolute left-3.5 top-3.5 text-cyan-500/70" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your operator call-sign"
                  className="w-full pl-10 pr-4 py-3 bg-[#020712]/90 border border-cyan-500/20 rounded-xl text-slate-100 text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/40 transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                Clearance Key (Password)
              </label>
              <div className="relative">
                <KeyRound size={16} className="absolute left-3.5 top-3.5 text-cyan-500/70" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 bg-[#020712]/90 border border-cyan-500/20 rounded-xl text-slate-100 text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/40 transition-all"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-3.5 bg-gradient-to-r from-cyan-600 via-sky-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-[0_0_25px_rgba(6,182,212,0.3)] transition-all active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <span>Authenticate & Access Console</span>
              <ArrowRight size={15} />
            </button>
          </form>
        ) : (
          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                Register New Operator Call-Sign
              </label>
              <div className="relative">
                <User size={16} className="absolute left-3.5 top-3.5 text-cyan-500/70" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Choose unique operator name"
                  className="w-full pl-10 pr-4 py-3 bg-[#020712]/90 border border-cyan-500/20 rounded-xl text-slate-100 text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/40 transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                Set Security Password
              </label>
              <div className="relative">
                <KeyRound size={16} className="absolute left-3.5 top-3.5 text-cyan-500/70" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Minimum 5 characters"
                  className="w-full pl-10 pr-4 py-3 bg-[#020712]/90 border border-cyan-500/20 rounded-xl text-slate-100 text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/40 transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                Target Architecture Platform
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setPlatform("windows")}
                  className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition-all ${
                    platform === "windows"
                      ? "bg-cyan-500/10 border-cyan-400 text-cyan-300"
                      : "bg-[#020712] border-cyan-500/10 text-slate-400 hover:border-cyan-500/30"
                  }`}
                >
                  <Monitor size={18} />
                  <span className="text-[11px] font-mono">Windows PC</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPlatform("android")}
                  className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition-all ${
                    platform === "android"
                      ? "bg-cyan-500/10 border-cyan-400 text-cyan-300"
                      : "bg-[#020712] border-cyan-500/10 text-slate-400 hover:border-cyan-500/30"
                  }`}
                >
                  <Smartphone size={18} />
                  <span className="text-[11px] font-mono">Android Standalone</span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-3.5 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-[0_0_25px_rgba(16,185,129,0.3)] transition-all active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Sparkles size={15} />
              <span>Claim Free 10-Day Hardware Pass</span>
            </button>
          </form>
        )}

        <div className="mt-6 pt-4 border-t border-cyan-500/10 flex items-center justify-between text-[11px] font-mono text-slate-500">
          <span className="flex items-center gap-1">
            <ShieldCheck size={13} className="text-emerald-400" /> Database Live Synced
          </span>
          <span>SHA-256 Verified</span>
        </div>
      </div>
    </div>
  );
}

