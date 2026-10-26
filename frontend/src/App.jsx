import React, { useState } from 'react';
import AuthModal from './components/AuthModal';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);

  return (
    <div className="relative min-h-screen bg-[#020612] text-slate-100 font-sans selection:bg-cyan-500 selection:text-black overflow-x-hidden">
      {/* Background Ambient Glow & Grid Lines */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-cyan-600/10 rounded-full blur-[140px]" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[300px] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-25" />
      </div>

      {/* Main Container */}
      <div className="relative z-10 flex flex-col min-h-screen">
        <main className="flex-1 flex flex-col justify-center">
          {!currentUser && <AuthModal onLogin={setCurrentUser} />}
          
          {currentUser && currentUser.role === 'admin' && (
            <AdminPanel user={currentUser} onLogout={() => setCurrentUser(null)} />
          )}
          
          {currentUser && currentUser.role === 'user' && (
            <Dashboard user={currentUser} onLogout={() => setCurrentUser(null)} />
          )}
        </main>

        {/* Global Footer */}
        <footer className="py-4 border-t border-cyan-500/10 text-center text-xs text-slate-500 font-mono">
          <p>
            GARUDA OS &copy; {new Date().getFullYear()} &bull; Engineered & Developed by{' '}
            <span className="text-cyan-400 font-medium">Suraj</span>
          </p>
        </footer>
      </div>
    </div>
  );
}