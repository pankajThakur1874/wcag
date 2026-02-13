'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Project } from '@/lib/types';

export default function ScanPage() {
    const [activeTab, setActiveTab] = useState<'quick' | 'project'>('quick');
    const [scanning, setScanning] = useState(false);
    const [progress, setProgress] = useState(0);
    const [scanStatus, setScanStatus] = useState('');
    const [scanResult, setScanResult] = useState<{ score?: number; issuesCount?: number } | null>(null);
    const [projects, setProjects] = useState<Project[]>([]);
    const [error, setError] = useState('');

    // Load projects for the project scan dropdown
    useEffect(() => {
        const loadProjects = async () => {
            try {
                const response = await api.getProjects({ limit: 100 });
                const data = response.data;
                if (Array.isArray(data)) {
                    setProjects(data);
                } else if (data?.items && Array.isArray(data.items)) {
                    setProjects(data.items);
                } else {
                    setProjects([]);
                }
            } catch (err) {
                console.error('Failed to load projects:', err);
            }
        };
        loadProjects();
    }, []);

    const pollScanStatus = useCallback(async (scanId: string) => {
        const poll = async () => {
            try {
                const response = await api.getScanStatus(scanId);
                const data = response.data;

                const pct = data.progress?.percentage ?? 0;
                setProgress(pct);
                setScanStatus(data.status);

                if (data.status === 'completed') {
                    setProgress(100);
                    setScanResult({ score: data.score, issuesCount: data.issuesCount });
                    setScanning(false);
                    return;
                }

                if (data.status === 'failed') {
                    setError('Scan failed. Please try again.');
                    setScanning(false);
                    return;
                }

                // Keep polling
                setTimeout(poll, 2000);
            } catch (err) {
                console.error('Poll error:', err);
                setError('Lost connection to scan. Check the Scans page for status.');
                setScanning(false);
            }
        };

        poll();
    }, []);

    const startQuickScan = async () => {
        setError('');
        setScanResult(null);
        const urlInput = document.querySelector<HTMLInputElement>('input[name="scanUrl"]');
        const url = urlInput?.value?.trim();
        if (!url) { setError('Please enter a URL'); return; }

        setScanning(true);
        setProgress(0);
        setScanStatus('queued');

        try {
            const response = await api.startQuickScan({ url });
            pollScanStatus(response.data.scanId);
        } catch (err: any) {
            setError(err.response?.data?.error?.message || 'Failed to start scan');
            setScanning(false);
        }
    };

    const startProjectScan = async () => {
        setError('');
        setScanResult(null);
        const projectSelect = document.querySelector<HTMLSelectElement>('select[name="projectId"]');
        const projectId = projectSelect?.value;
        if (!projectId) { setError('Please select a project'); return; }

        setScanning(true);
        setProgress(0);
        setScanStatus('queued');

        try {
            const response = await api.startProjectScan({ projectId });
            pollScanStatus(response.data.scanId);
        } catch (err: any) {
            setError(err.response?.data?.error?.message || 'Failed to start scan');
            setScanning(false);
        }
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
                                <input type="url" name="scanUrl" className="auth-input" style={{ margin: 0 }} placeholder="https://example.com" />
                                <button className="btn-gradient" onClick={startQuickScan} disabled={scanning}>
                                    {scanning ? 'Scanning...' : 'Start Scan'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Project Scan Form */}
                {activeTab === 'project' && (
                    <div>
                        <div style={{ marginBottom: '2rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Select Project</label>
                            <select name="projectId" className="form-select" style={{ marginBottom: '1rem' }}>
                                <option value="">-- Select Project --</option>
                                {projects.map((p) => (
                                    <option key={p.id} value={p.id}>{p.name} ({p.url})</option>
                                ))}
                            </select>
                            <button className="btn-gradient" onClick={startProjectScan} disabled={scanning}>
                                {scanning ? 'Scanning...' : 'Start Project Scan'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Error */}
                {error && (
                    <div style={{ color: 'red', padding: '0.75rem', background: '#fef2f2', borderRadius: 'var(--radius-md)', marginTop: '1rem' }}>
                        {error}
                    </div>
                )}

                {/* Progress */}
                {scanning && (
                    <div style={{ marginTop: '2rem', background: '#f8fafc', padding: '1.5rem', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span>{scanStatus === 'completed' ? 'Scan Complete!' : `Scanning... (${scanStatus})`}</span>
                            <span>{progress}%</span>
                        </div>
                        <div style={{ height: '10px', background: '#e2e8f0', borderRadius: '5px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${progress}%`, background: 'var(--primary-gradient)', transition: 'width 0.3s' }} />
                        </div>
                    </div>
                )}

                {/* Scan Result */}
                {scanResult && (
                    <div style={{ marginTop: '2rem', padding: '1.5rem', background: '#ecfdf5', borderRadius: 'var(--radius-md)', border: '1px solid #a7f3d0' }}>
                        <h3 style={{ color: '#065f46', marginBottom: '0.5rem' }}>✅ Scan Complete!</h3>
                        <p style={{ color: '#047857' }}>
                            Score: <strong>{scanResult.score ?? '–'}%</strong> • Issues found: <strong>{scanResult.issuesCount ?? 0}</strong>
                        </p>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                            View detailed results on the Issues or Reports page.
                        </p>
                    </div>
                )}
            </div>
        </>
    );
}
