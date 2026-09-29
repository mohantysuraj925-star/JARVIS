import React, { useState } from 'react';
import { Eye, EyeOff, ShieldCheck, User, KeyRound } from 'lucide-react';

export default function AuthModal({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username || password.length < 5) {
      setError('Password must be at least 5 characters');
      return;
    }
    setError('');
    // Master Admin or Regular User Handshake
    if (username === 'admin123' && password === 'Suraj') {
      onLogin({ username, role: 'admin' });
    } else {
      onLogin({ username, role: 'user', days_remaining: 10 });
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh] px-4">
      <div className="w-full max-w-md p-8 bg-white/70 backdrop-blur-xl border border-white/80 rounded-2xl shadow-xl">
        <div className="text-center mb-6">
          <div className="inline-flex p-3 bg-blue-50 text-blue-600 rounded-full mb-3 shadow-inner">
            <ShieldCheck size={32} />
          </div>
          <h2 className="text-2xl font-bold text-slate-800">JARVIS by Suraj</h2>
          <p className="text-sm text-slate-500 mt-1">Official Security & Licensing Gateway</p>
        </div>

        <div className="flex border-b border-slate-200 mb-6">
          <button
            onClick={() => setIsRegister(false)}
            className={`flex-1 pb-2 font-medium text-sm transition-colors ${!isRegister ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-400'}`}
          >
            Sign In
          </button>
          <button
            onClick={() => setIsRegister(true)}
            className={`flex-1 pb-2 font-medium text-sm transition-colors ${isRegister ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-400'}`}
          >
            Create Account
          </button>
        </div>

        {error && <div className="mb-4 text-xs text-red-500 bg-red-50 p-2.5 rounded-lg border border-red-100">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Username</label>
            <div className="relative">
              <User size={18} className="absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter unique username"
                className="w-full pl-10 pr-4 py-2.5 bg-white/60 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-700 text-sm"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Password</label>
            <div className="relative">
              <KeyRound size={18} className="absolute left-3 top-3 text-slate-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="5 to 8 characters"
                className="w-full pl-10 pr-10 py-2.5 bg-white/60 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-700 text-sm"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-md shadow-blue-500/20 transition-all text-sm mt-2"
          >
            {isRegister ? 'Register & Claim 10-Day Pass' : 'Authenticate Session'}
          </button>
        </form>
      </div>
    </div>
  );
}