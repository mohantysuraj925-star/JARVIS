import React, { useState } from 'react';
import AuthModal from './components/AuthModal';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 font-sans text-slate-800">
      {!currentUser && <AuthModal onLogin={setCurrentUser} />}
      {currentUser && currentUser.role === 'admin' && (
        <AdminPanel onLogout={() => setCurrentUser(null)} />
      )}
      {currentUser && currentUser.role === 'user' && (
        <Dashboard user={currentUser} onLogout={() => setCurrentUser(null)} />
      )}
    </div>
  );
}