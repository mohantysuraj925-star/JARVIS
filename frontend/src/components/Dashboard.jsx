import React from 'react';
import { Monitor, Smartphone, ShieldAlert, LogOut, CheckCircle } from 'lucide-react';

export default function Dashboard({ user, onLogout }) {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Top Navbar */}
      <header className="flex justify-between items-center p-4 bg-white/70 backdrop-blur-xl border border-white/80 rounded-2xl shadow-sm mb-8">
        <div>
          <h1 className="text-xl font-bold text-slate-800">JARVIS OS Portal</h1>
          <p className="text-xs text-slate-500">Welcome, {user.username}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-600 text-xs font-semibold rounded-full border border-emerald-100">
            <CheckCircle size={14} /> 10-Day Free Trial Active
          </span>
          <button
            onClick={onLogout}
            className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* Hero Notice */}
      <section className="p-6 bg-white/60 backdrop-blur-lg border border-white/80 rounded-2xl shadow-sm mb-8">
        <h2 className="text-lg font-bold text-slate-800 mb-2">Project Terms & Licensing</h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          Developed and curated exclusively by <strong>Suraj</strong>. This intelligent assistant software is authorized 
          for personal, educational, and evaluation purposes under the active 10-day hardware license. Redistribution, 
          code de-compilation, or commercial monetization without express written permission is restricted by copyright policy.
        </p>
      </section>

      {/* Download Hub */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-6 bg-white/70 backdrop-blur-xl border border-white/80 rounded-2xl shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
          <div>
            <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl w-fit mb-4">
              <Monitor size={28} />
            </div>
            <h3 className="text-base font-bold text-slate-800">JARVIS for Windows PC</h3>
            <p className="text-xs text-slate-500 mt-1">Standalone desktop launcher with hardware-locked verification.</p>
          </div>
          <a
            href="http://127.0.0.1:8000/download/windows"
            className="mt-6 inline-flex items-center justify-center gap-2 w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-xl transition-all"
          >
            Download Windows Setup
          </a>
        </div>

        <div className="p-6 bg-white/70 backdrop-blur-xl border border-white/80 rounded-2xl shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
          <div>
            <div className="p-3 bg-sky-50 text-sky-600 rounded-xl w-fit mb-4">
              <Smartphone size={28} />
            </div>
            <h3 className="text-base font-bold text-slate-800">JARVIS Mobile Hub (APK)</h3>
            <p className="text-xs text-slate-500 mt-1">Optimized client featuring lightweight socket streaming.</p>
          </div>
          <a
            href="http://127.0.0.1:8000/download/android"
            className="mt-6 inline-flex items-center justify-center gap-2 w-full py-2.5 bg-sky-600 hover:bg-sky-700 text-white text-sm font-medium rounded-xl transition-all"
          >
            Download Android APK
          </a>
        </div>
      </div>
    </div>
  );
}