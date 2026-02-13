'use client';

import { useState } from "react";

export default function ScanPage() {
    const [activeTab, setActiveTab] = useState<'quick' | 'project'>('quick');
    const [scanning, setScanning] = useState(false);
    const [progress, setProgress] = useState(0);

    const startScan = () => {
        setScanning(true);
        setProgress(0);
        let p = 0;
        const interval = setInterval(() => {
            p += Math.random() * 15;
            if (p >= 100) { p = 100; clearInterval(interval); }
            setProgress(Math.round(p));
        }, 400);
    };

    return (
        <>
            <header className="section-header">
                <h1 className="section-title">New Scan</h1>
                <p className="section-subtitle">Run an accessibility audit.</p>
            </header>

            <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
                {/* Tabs */}
                <div style={{ display: 'flex', borderBottom: '1px solid var(--border-light)', marginBottom: '2rem' }}>
                    <div
                        className={`nav-item ${activeTab === 'quick' ? 'active' : ''}`}
                        style={{ borderRadius: 0, borderBottom: activeTab === 'quick' ? '2px solid var(--primary-start)' : '2px solid transparent', background: activeTab === 'quick' ? 'transparent' : undefined, color: activeTab === 'quick' ? 'var(--primary-start)' : undefined, boxShadow: 'none' }}
                        onClick={() => setActiveTab('quick')}
                    >Quick Scan</div>
                    <div
                        className={`nav-item ${activeTab === 'project' ? 'active' : ''}`}
                        style={{ borderRadius: 0, borderBottom: activeTab === 'project' ? '2px solid var(--primary-start)' : '2px solid transparent', background: activeTab === 'project' ? 'transparent' : undefined, color: activeTab === 'project' ? 'var(--primary-start)' : undefined, boxShadow: 'none' }}
                        onClick={() => setActiveTab('project')}
                    >Project Scan</div>
                </div>

                {/* Quick Scan Form */}
                {activeTab === 'quick' && (
                    <div>
                        <div style={{ marginBottom: '2rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Website URL</label>
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <input type="url" className="auth-input" style={{ margin: 0 }} placeholder="https://example.com" defaultValue="https://example.com" />
                                <button className="btn-gradient" onClick={startScan}>Start Scan</button>
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
                            <div>
                                <label style={{ fontWeight: 500, marginRight: '1rem' }}>Site-Wide Scan</label>
                                <label style={{ position: 'relative', display: 'inline-block', width: '50px', height: '26px' }}>
                                    <input type="checkbox" style={{ opacity: 0, width: 0, height: 0 }} />
                                    <span style={{ position: 'absolute', cursor: 'pointer', inset: 0, backgroundColor: '#cbd5e1', borderRadius: '34px', transition: '.4s' }} />
                                </label>
                            </div>
                            <div>
                                <label style={{ fontSize: '0.9rem', display: 'block' }}>Max Pages</label>
                                <select style={{ padding: '0.4rem', borderRadius: '6px', border: '1px solid var(--border-light)', fontFamily: 'inherit' }}>
                                    <option value="10">10</option>
                                    <option value="50">50</option>
                                    <option value="100">100</option>
                                </select>
                            </div>
                        </div>
                    </div>
                )}

                {/* Project Scan Form */}
                {activeTab === 'project' && (
                    <div>
                        <div style={{ marginBottom: '2rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Select Project</label>
                            <select className="form-select">
                                <option value="">-- Select Project --</option>
                                <option value="1">Corporate Website</option>
                                <option value="2">E-commerce App</option>
                                <option value="3">Gov Portal</option>
                            </select>
                            <button className="btn-gradient" onClick={startScan}>Start Project Scan</button>
                        </div>
                    </div>
                )}

                {/* Progress */}
                {scanning && (
                    <div style={{ marginTop: '2rem', background: '#f8fafc', padding: '1.5rem', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span>{progress >= 100 ? 'Scan Complete!' : 'Scanning...'}</span>
                            <span>{progress}%</span>
                        </div>
                        <div style={{ height: '10px', background: '#e2e8f0', borderRadius: '5px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${progress}%`, background: 'var(--primary-gradient)', transition: 'width 0.3s' }} />
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
