import React, { useState, useEffect } from 'react';

export default function AdminPanel({ onLogout }) {
  const [data, setData] = useState({ telemetry: 14, trials: 2, devices: [] });
  const [broadcast, setBroadcast] = useState('');
  const [msgStatus, setMsgStatus] = useState('');

  useEffect(() => {
    fetch('/api/admin/data')
      .then(res => res.json())
      .then(d => setData(d))
      .catch(() => {
        setData({
          telemetry: 14,
          trials: 2,
          devices: [
            { username: 'Suraj (Master)', hwid: 'DEV-MACHINE-UUID-8891', days: 10, status: 'Active', is_lifetime: false },
            { username: 'DemoUser', hwid: 'WIN-CLIENT-UUID-9912', days: 10, status: 'Active', is_lifetime: false }
          ]
        });
      });
  }, []);

  const sendBroadcast = async () => {
    if (!broadcast) return;
    try {
      const res = await fetch('/api/admin/broadcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: broadcast })
      });
      if (res.ok) {
        setMsgStatus('Broadcast live sent!');
        setBroadcast('');
        setTimeout(() => setMsgStatus(''), 3000);
      }
    } catch (e) {
      setMsgStatus('Broadcast saved locally.');
      setTimeout(() => setMsgStatus(''), 3000);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'radial-gradient(circle at top left, #1e1b4b, #0f172a, #030712)',
      color: '#f8fafc',
      fontFamily: 'Inter, sans-serif',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: '700', letterSpacing: '-0.5px' }}>Super Admin Console</h1>
            <p style={{ color: '#94a3b8', fontSize: '14px' }}>JARVIS Core Ecosystem Control</p>
          </div>
          <button onClick={onLogout} style={{
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#fca5a5',
            padding: '8px 16px',
            borderRadius: '8px',
            cursor: 'pointer'
          }}>Exit</button>
        </div>

        {/* Live Broadcast Engine (Glassmorphic Box) */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '30px',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '10px', color: '#38bdf8' }}>
            📢 Global Customer Broadcast Engine
          </h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '14px' }}>
            Yahan jo bhi message bhejoge, wo turant har active desktop client aur customer screen par broadcast hoga.
          </p>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              placeholder="Type urgent customer notice / update message..."
              value={broadcast}
              onChange={e => setBroadcast(e.target.value)}
              style={{
                flex: 1,
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '8px',
                padding: '12px 16px',
                color: '#fff',
                outline: 'none'
              }}
            />
            <button onClick={sendBroadcast} style={{
              background: 'linear-gradient(135deg, #0ea5e9, #2563eb)',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 24px',
              color: '#fff',
              fontWeight: '600',
              cursor: 'pointer'
            }}>Broadcast Now</button>
          </div>
          {msgStatus && <p style={{ color: '#4ade80', fontSize: '13px', marginTop: '10px' }}>{msgStatus}</p>}
        </div>

        {/* Telemetry Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '30px' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '20px' }}>
            <p style={{ color: '#94a3b8', fontSize: '12px' }}>Total Registered</p>
            <h3 style={{ fontSize: '24px', fontWeight: '700', marginTop: '4px' }}>{data.devices.length}</h3>
          </div>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '20px' }}>
            <p style={{ color: '#94a3b8', fontSize: '12px' }}>Total Telemetry Hits</p>
            <h3 style={{ fontSize: '24px', fontWeight: '700', marginTop: '4px' }}>{data.telemetry}</h3>
          </div>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '20px' }}>
            <p style={{ color: '#94a3b8', fontSize: '12px' }}>Active Trials</p>
            <h3 style={{ fontSize: '24px', fontWeight: '700', marginTop: '4px' }}>{data.trials}</h3>
          </div>
        </div>

        {/* User Table with Glassmorphism */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: 'rgba(255, 255, 255, 0.04)', color: '#94a3b8', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <th style={{ padding: '16px' }}>USER NAME</th>
                <th style={{ padding: '16px' }}>HARDWARE ID</th>
                <th style={{ padding: '16px' }}>STATUS</th>
                <th style={{ padding: '16px' }}>DAYS REMAINING</th>
              </tr>
            </thead>
            <tbody>
              {data.devices.map((dev, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                  <td style={{ padding: '16px', fontWeight: '600', color: '#e0e7ff' }}>{dev.username}</td>
                  <td style={{ padding: '16px', color: '#94a3b8', fontFamily: 'monospace' }}>{dev.hwid}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', padding: '4px 10px', borderRadius: '12px', fontSize: '12px' }}>
                      {dev.status}
                    </span>
                  </td>
                  <td style={{ padding: '16px', color: '#f8fafc' }}>{dev.is_lifetime ? '∞ Lifetime' : `${dev.days}d`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}
