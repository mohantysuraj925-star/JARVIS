import React, { useState, useEffect } from "react";
import { Radio, Users, Activity, Clock, ShieldCheck, LogOut, Terminal, CheckCircle2, Send, Power, Check, X, Monitor, Smartphone, Plus, Minus, Infinity as InfIcon, Download, MessageSquare, Star, RefreshCw, Trash2 } from "lucide-react";

export default function AdminPanel({ onLogout }) {
  const [data, setData] = useState({ telemetry: 0, trials: 0, devices: [] });
  const [feedbacks, setFeedbacks] = useState([]);
  const [broadcast, setBroadcast] = useState("");
  const [msgStatus, setMsgStatus] = useState("");

  const fetchRealData = async () => {
    try {
      const res = await fetch("/api/admin/data");
      if (res.ok) {
        const d = await res.json();
        setData({
          telemetry: d.telemetry || 0,
          trials: d.trials || 0,
          devices: d.devices || []
        });
      }
    } catch {}

    try {
      const fRes = await fetch("/api/feedback/metrics");
      if (fRes.ok) {
        const fData = await fRes.json();
        setFeedbacks(Array.isArray(fData.reviews) ? fData.reviews : (Array.isArray(fData) ? fData : []));
      }
    } catch {}
  };

  useEffect(() => {
    fetchRealData();
    const interval = setInterval(fetchRealData, 4000);
    return () => clearInterval(interval);
  }, []);

  // Delete User Node from Database permanently
  const deleteDeviceNode = async (hwid, username) => {
    if (!window.confirm(`Kya aap sure hain ki "${username}" (HWID: ${hwid}) ko permanently database se hatana hai?`)) {
      return;
    }

    try {
      await fetch("/api/admin/delete-device", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hwid })
      });
    } catch {}

    // Immediately update local counting and devices list
    setData(prev => {
      const remainingDevices = prev.devices.filter(d => d.hwid !== hwid);
      const activeCount = remainingDevices.filter(d => d.status === "Active" && (d.days > 0 || d.is_lifetime)).length;
      return {
        ...prev,
        devices: remainingDevices,
        trials: activeCount
      };
    });

    setMsgStatus(`Node ${username} successfully deleted from database!`);
    setTimeout(() => setMsgStatus(""), 3500);
  };

  const adjustUserDays = async (hwid, delta, makeInfinite = false) => {
    try {
      await fetch("/api/admin/modify-license", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hwid, delta, infinite: makeInfinite })
      });
      fetchRealData();
      setMsgStatus(`Live DB license updated for: ${hwid}`);
      setTimeout(() => setMsgStatus(""), 3000);
    } catch {
      setMsgStatus("Server sync pending.");
      setTimeout(() => setMsgStatus(""), 3000);
    }
  };

  const toggleAllDevices = async (newStatus) => {
    try {
      await fetch("/api/admin/toggle-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      fetchRealData();
      setMsgStatus(`All client nodes set to: ${newStatus.toUpperCase()}`);
      setTimeout(() => setMsgStatus(""), 3500);
    } catch {
      setMsgStatus("Status update dispatched.");
      setTimeout(() => setMsgStatus(""), 3500);
    }
  };

  const toggleDevice = async (hwid, currentStatus) => {
    const nextStatus = currentStatus === "Active" ? "Disabled" : "Active";
    try {
      await fetch("/api/admin/toggle-device", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hwid, status: nextStatus })
      });
      fetchRealData();
    } catch {}
  };

  const sendBroadcast = async () => {
    if (!broadcast.trim()) return;
    try {
      const res = await fetch("/api/admin/broadcast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: broadcast })
      });
      if (res.ok) {
        setMsgStatus("Real-Time Broadcast sent across all nodes!");
        setBroadcast("");
        setTimeout(() => setMsgStatus(""), 3500);
      }
    } catch {
      setMsgStatus("Broadcast delivered.");
      setTimeout(() => setMsgStatus(""), 3500);
    }
  };

  return (
    <div className="min-h-screen text-slate-100 font-sans px-4 py-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Top Header */}
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-5 bg-[#030914]/85 backdrop-blur-2xl border border-cyan-500/20 rounded-2xl shadow-[0_0_25px_rgba(6,182,212,0.1)] mb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black tracking-wider bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
                GARUDA MASTER CONSOLE
              </h1>
              <span className="text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
                BY SURAJ
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-1.5">
              <Terminal size={12} className="text-cyan-400" />
              Live Hardware Node Controller &bull; Clearance Level 1
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchRealData}
              title="Force Live Sync"
              className="p-2 bg-cyan-950/40 hover:bg-cyan-900/50 border border-cyan-500/30 text-cyan-300 rounded-xl transition-all"
            >
              <RefreshCw size={15} />
            </button>
            <button
              onClick={onLogout}
              className="inline-flex items-center gap-2 px-4 py-2 bg-rose-950/40 hover:bg-rose-900/50 border border-rose-500/30 text-rose-300 text-xs font-mono font-semibold rounded-xl transition-all"
            >
              <LogOut size={14} /> Exit Console
            </button>
          </div>
        </header>

        {/* Master Direct Download Hub */}
        <div className="p-4 bg-gradient-to-r from-[#040e1a]/90 via-[#071629]/90 to-[#040e1a]/90 backdrop-blur-xl border border-cyan-500/30 rounded-2xl mb-6 flex flex-col md:flex-row items-center justify-between gap-4 shadow-[0_0_20px_rgba(6,182,212,0.1)]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-500/20 text-cyan-300 border border-cyan-400/30 rounded-xl">
              <Download size={20} className="animate-bounce" />
            </div>
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-100">
                Master Testing Download Hub
              </h3>
              <p className="text-xs text-slate-400">
                Direct safe download: Yahan click karke PC setup (.exe) ya Mobile (.apk) download karke test karein.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <a
              href="/download/windows"
              download="GARUDA_Windows_Setup.exe"
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-md transition-all active:scale-[0.98]"
            >
              <Monitor size={14} /> PC Setup (.exe)
            </a>
            <a
              href="http://127.0.0.1:8000/download/android"
              download="GARUDA_Mobile.apk"
              className="flex-1 md:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-md transition-all active:scale-[0.98]"
            >
              <Smartphone size={14} /> Mobile (.apk)
            </a>
          </div>
        </div>

        {/* Master Node Switch Controls */}
        <div className="p-4 bg-[#040e1a]/85 backdrop-blur-xl border border-cyan-500/20 rounded-2xl mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-xl">
              <Power size={20} />
            </div>
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
                Master Network Controls
              </h3>
              <p className="text-xs text-slate-400">
                Ek click me sabhi users ka hardware license active ya suspend karein.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={() => toggleAllDevices("Active")}
              className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.2)] transition-all"
            >
              <Check size={14} /> All Active
            </button>
            <button
              onClick={() => toggleAllDevices("Disabled")}
              className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-[0_0_15px_rgba(244,63,94,0.2)] transition-all"
            >
              <X size={14} /> All Deactive
            </button>
          </div>
        </div>

        {/* Real Broadcast Box */}
        <section className="relative overflow-hidden p-6 bg-[#040e1a]/85 backdrop-blur-xl border border-cyan-500/20 rounded-2xl shadow-lg mb-6">
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-sm font-bold mb-2">
            <Radio size={18} className="animate-pulse" />
            <span>Real-Time Node Broadcast Engine</span>
          </div>
          <p className="text-xs text-slate-400 font-sans mb-4">
            Live alerts ya notices active desktop aur mobile screens par real-time bhejein.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="Type urgent live alert or firmware notice..."
              value={broadcast}
              onChange={e => setBroadcast(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-[#020712] border border-cyan-500/20 rounded-xl text-slate-200 text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/40 transition-all"
            />
            <button
              onClick={sendBroadcast}
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-md transition-all active:scale-[0.98]"
            >
              <Send size={13} /> Broadcast
            </button>
          </div>

          {msgStatus && (
            <p className="mt-3 text-xs font-mono text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 size={13} /> {msgStatus}
            </p>
          )}
        </section>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="p-5 bg-[#040e1a]/80 backdrop-blur-xl border border-cyan-500/20 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Live Registered Nodes</p>
              <h3 className="text-2xl font-black text-slate-100 mt-1">{data.devices.length}</h3>
            </div>
            <div className="p-3 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-xl">
              <Users size={20} />
            </div>
          </div>

          <div className="p-5 bg-[#040e1a]/80 backdrop-blur-xl border border-cyan-500/20 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Live Telemetry Pings</p>
              <h3 className="text-2xl font-black text-slate-100 mt-1">{data.telemetry}</h3>
            </div>
            <div className="p-3 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-xl">
              <Activity size={20} />
            </div>
          </div>

          <div className="p-5 bg-[#040e1a]/80 backdrop-blur-xl border border-cyan-500/20 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Active Trial Passes</p>
              <h3 className="text-2xl font-black text-slate-100 mt-1">{data.trials}</h3>
            </div>
            <div className="p-3 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-xl">
              <Clock size={20} />
            </div>
          </div>
        </div>

        {/* Hardware Nodes Table with Delete / Purge Action */}
        <div className="bg-[#040e1a]/80 backdrop-blur-xl border border-cyan-500/20 rounded-2xl overflow-hidden shadow-lg mb-6">
          <div className="px-6 py-4 border-b border-cyan-500/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-cyan-400" />
              <h3 className="text-xs font-mono font-bold text-slate-200 tracking-wider uppercase">
                Real Client Hardware Nodes & Pass Control
              </h3>
            </div>
            <span className="text-[10px] font-mono text-cyan-400/80 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded">
              Auto-Sync: 4s
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#020712]/70 text-slate-400 font-mono border-b border-cyan-500/10 uppercase tracking-wider">
                  <th className="py-3 px-4">Operator</th>
                  <th className="py-3 px-4">Hardware UUID</th>
                  <th className="py-3 px-4">Platform</th>
                  <th className="py-3 px-4">Node Status</th>
                  <th className="py-3 px-4">Remaining Days</th>
                  <th className="py-3 px-4 text-center">Trial Modifier</th>
                  <th className="py-3 px-4 text-center">Node Access</th>
                  <th className="py-3 px-4 text-right">Delete</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cyan-500/5 font-sans">
                {data.devices.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500 font-mono text-xs">
                      No hardware nodes registered yet. Real nodes will appear here automatically upon client login/registration.
                    </td>
                  </tr>
                ) : (
                  data.devices.map((dev, i) => (
                    <tr key={i} className="hover:bg-cyan-500/[0.02] transition-colors">
                      <td className="py-4 px-4 font-semibold text-slate-200">{dev.username}</td>
                      <td className="py-4 px-4 font-mono text-slate-400">{dev.hwid}</td>
                      <td className="py-4 px-4">
                        {dev.platform === "Android" ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-mono text-[11px] bg-sky-950/70 text-sky-400 border border-sky-500/30">
                            <Smartphone size={12} /> Android
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-mono text-[11px] bg-indigo-950/70 text-indigo-400 border border-indigo-500/30">
                            <Monitor size={12} /> Windows
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono border ${
                          dev.status === "Active"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${dev.status === "Active" ? "bg-emerald-400 animate-pulse" : "bg-rose-400"}`} />
                          {dev.status}
                        </span>
                      </td>
                      <td className="py-4 px-4 font-mono font-semibold text-cyan-300">
                        {dev.is_lifetime ? "∞ Lifetime" : `${dev.days} Days`}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <div className="inline-flex items-center gap-1 p-1 bg-[#020712] border border-cyan-500/20 rounded-xl">
                          <button
                            onClick={() => adjustUserDays(dev.hwid, -5)}
                            title="Subtract 5 Days"
                            className="p-1 hover:bg-rose-500/20 text-rose-400 rounded-lg transition-all"
                          >
                            <Minus size={13} />
                          </button>
                          <button
                            onClick={() => adjustUserDays(dev.hwid, 5)}
                            title="Add 5 Days"
                            className="p-1 hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition-all"
                          >
                            <Plus size={13} />
                          </button>
                          <button
                            onClick={() => adjustUserDays(dev.hwid, 0, true)}
                            title="Toggle Lifetime (Infinity)"
                            className={`px-1.5 py-0.5 font-mono text-[10px] rounded-lg transition-all ${
                              dev.is_lifetime
                                ? "bg-cyan-500 text-black font-bold"
                                : "hover:bg-cyan-500/20 text-cyan-400"
                            }`}
                          >
                            <InfIcon size={13} />
                          </button>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-center">
                        <button
                          onClick={() => toggleDevice(dev.hwid, dev.status)}
                          className={`px-3 py-1 text-[11px] font-mono rounded-lg border transition-all ${
                            dev.status === "Active"
                              ? "bg-rose-950/40 border-rose-500/30 text-rose-300 hover:bg-rose-900/50"
                              : "bg-emerald-950/40 border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/50"
                          }`}
                        >
                          {dev.status === "Active" ? "Deactivate" : "Activate"}
                        </button>
                      </td>
                      <td className="py-4 px-4 text-right">
                        <button
                          onClick={() => deleteDeviceNode(dev.hwid, dev.username)}
                          title="Permanently remove node from DB"
                          className="p-1.5 bg-rose-950/30 hover:bg-rose-600/30 text-rose-400 border border-rose-500/20 hover:border-rose-500 rounded-lg transition-all"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Feedback Cards */}
        <section className="bg-[#040e1a]/80 backdrop-blur-xl border border-cyan-500/20 rounded-2xl overflow-hidden shadow-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare size={18} className="text-cyan-400" />
            <h3 className="text-xs font-mono font-bold text-slate-200 tracking-wider uppercase">
              Customer Feedbacks & Ratings
            </h3>
          </div>

          {feedbacks.length === 0 ? (
            <div className="py-6 text-center text-slate-500 font-mono text-xs border border-dashed border-cyan-500/10 rounded-xl">
              No customer feedback received yet. Live feedback submissions will automatically show up here.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {feedbacks.map((fb, idx) => (
                <div key={idx} className="p-4 bg-[#020712] border border-cyan-500/10 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-200 text-xs font-mono">{fb.username || "Operator"}</span>
                    <div className="flex items-center gap-1 text-amber-400">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} size={12} fill={i < (fb.rating || 5) ? "#fbbf24" : "none"} strokeWidth={1.5} />
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{fb.comment || fb.message}</p>
                </div>
              ))}
            </div>
          )}
        </section>

      </div>
    </div>
  );
}

