'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast-context';
import type { Project } from '@/lib/types';

// Recommended scanners for quick scans (fast and reliable)
const RECOMMENDED_SCANNERS = ['axe', 'html_validator', 'contrast', 'keyboard', 'aria'];

// All available scanners
const ALL_SCANNERS = [
    { id: 'axe', name: 'Axe Core', category: 'Core' },
    { id: 'pa11y', name: 'Pa11y', category: 'Core' },
    { id: 'html_validator', name: 'HTML Validator', category: 'Core' },
    { id: 'contrast', name: 'Contrast Checker', category: 'Essential' },
    { id: 'keyboard', name: 'Keyboard Navigation', category: 'Essential' },
    { id: 'aria', name: 'ARIA Validator', category: 'Essential' },
    { id: 'forms', name: 'Forms Accessibility', category: 'Essential' },
    { id: 'image_alt', name: 'Image Alt Text', category: 'Content' },
    { id: 'link_text', name: 'Link Text', category: 'Content' },
    { id: 'readability', name: 'Readability', category: 'Content' },
    { id: 'media', name: 'Media Accessibility', category: 'Content' },
    { id: 'touch_target', name: 'Touch Target Size', category: 'Mobile' },
    { id: 'pointer_gestures', name: 'Pointer Gestures', category: 'Mobile' },
    { id: 'focus_obscured', name: 'Focus Not Obscured', category: 'WCAG 2.2' },
    { id: 'hover_content', name: 'Hover/Focus Content', category: 'WCAG 2.2' },
    { id: 'character_shortcuts', name: 'Character Key Shortcuts', category: 'WCAG 2.2' },
    { id: 'consistent_navigation', name: 'Consistent Navigation', category: 'Navigation' },
    { id: 'multiple_ways', name: 'Multiple Ways', category: 'Navigation' },
    { id: 'interactive', name: 'Interactive Elements', category: 'Navigation' },
    { id: 'lighthouse', name: 'Lighthouse', category: 'Advanced' },
    { id: 'seo', name: 'SEO Accessibility', category: 'Advanced' },
    { id: 'color_only', name: 'Color Only Information', category: 'Advanced' },
    { id: 'media_accessibility', name: 'Advanced Media', category: 'Advanced' },
];

export default function ScanPage() {
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<'quick' | 'project'>('quick');
    const [scanning, setScanning] = useState(false);
    const [progress, setProgress] = useState(0);
    const [scanStatus, setScanStatus] = useState('');
    const [scanResult, setScanResult] = useState<{ score?: number; issuesCount?: number } | null>(null);
    const [projects, setProjects] = useState<Project[]>([]);
    const [error, setError] = useState('');
    const [selectedScanners, setSelectedScanners] = useState<string[]>(RECOMMENDED_SCANNERS);
    const [showScannerModal, setShowScannerModal] = useState(false);
    const [currentScanId, setCurrentScanId] = useState<string | null>(null);
    const [currentUrl, setCurrentUrl] = useState<string | null>(null);
    const [pagesScanned, setPagesScanned] = useState(0);
    const [totalPages, setTotalPages] = useState(0);

    // Load projects for the project scan dropdown
    useEffect(() => {
        const loadProjects = async () => {
            try {
                const response = await api.getProjects({ limit: 100 });
                setProjects(response.data);
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
                setCurrentScanId(scanId);

                // Update progress details
                if (data.progress) {
                    setCurrentUrl(data.progress.currentUrl || null);
                    setPagesScanned(data.progress.pagesScanned || 0);
                    setTotalPages(data.progress.totalPages || 0);
                }

                if (data.status === 'completed') {
                    setProgress(100);
                    setScanResult({ score: data.score, issuesCount: data.issuesCount });
                    setScanning(false);
                    setCurrentUrl(null);
                    toast.success('Scan completed successfully!');
                    return;
                }

                if (data.status === 'failed') {
                    setError('Scan failed. Please try again.');
                    setScanning(false);
                    setCurrentUrl(null);
                    toast.error('Scan failed');
                    return;
                }

                // Keep polling
                setTimeout(poll, 2000);
            } catch (err) {
                console.error('Poll error:', err);
                setError('Lost connection to scan. Check the Scans page for status.');
                setScanning(false);
                setCurrentUrl(null);
                toast.error('Lost connection to scan');
            }
        };

        poll();
    }, [toast]);

    const startQuickScan = async () => {
        setError('');
        setScanResult(null);
        const urlInput = document.querySelector<HTMLInputElement>('input[name="scanUrl"]');
        const url = urlInput?.value?.trim();
        if (!url) { setError('Please enter a URL'); return; }
        if (selectedScanners.length === 0) { setError('Please select at least one scanner'); return; }

        setScanning(true);
        setProgress(0);
        setScanStatus('queued');

        try {
            const response = await api.startQuickScan({ url, scanners: selectedScanners });
            pollScanStatus(response.data.scanId);
        } catch (err: any) {
            setError(err.response?.data?.error?.message || 'Failed to start scan');
            setScanning(false);
        }
    };

    const toggleScanner = (scannerId: string) => {
        setSelectedScanners(prev =>
            prev.includes(scannerId)
                ? prev.filter(id => id !== scannerId)
                : [...prev, scannerId]
        );
    };

    const selectRecommended = () => {
        setSelectedScanners(RECOMMENDED_SCANNERS);
    };

    const selectAll = () => {
        setSelectedScanners(ALL_SCANNERS.map(s => s.id));
    };

    const cancelScan = () => {
        setScanning(false);
        setProgress(0);
        setScanStatus('');
        setCurrentScanId(null);
        setCurrentUrl(null);
        setPagesScanned(0);
        setTotalPages(0);
        toast.info('Scan cancelled');
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
                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Website URL</label>
                            <input type="url" name="scanUrl" className="auth-input" style={{ margin: 0 }} placeholder="https://example.com" />
                        </div>

                        {/* Scanner Selection */}
                        <div style={{ marginBottom: '2rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                <label style={{ fontWeight: 500 }}>Scanners ({selectedScanners.length} selected)</label>
                                <button
                                    type="button"
                                    onClick={() => setShowScannerModal(true)}
                                    style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}
                                >
                                    Configure Scanners
                                </button>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                {selectedScanners.map(scannerId => {
                                    const scanner = ALL_SCANNERS.find(s => s.id === scannerId);
                                    return (
                                        <span key={scannerId} style={{ fontSize: '0.75rem', background: '#e0e7ff', color: '#4c1d95', padding: '0.25rem 0.6rem', borderRadius: '0.25rem' }}>
                                            {scanner?.name || scannerId}
                                        </span>
                                    );
                                })}
                                {selectedScanners.length === 0 && (
                                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No scanners selected</span>
                                )}
                            </div>
                        </div>

                        <button className="btn-gradient" onClick={startQuickScan} disabled={scanning} style={{ width: '100%' }}>
                            {scanning ? 'Scanning...' : 'Start Quick Scan'}
                        </button>
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
                    <div style={{ marginTop: '2rem', background: 'linear-gradient(135deg, #f8fafc, #e0e7ff)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid #e0e7ff' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <div>
                                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--text-main)' }}>
                                    {scanStatus === 'completed' ? '✓ Scan Complete!' : '🔍 Scanning in Progress...'}
                                </h3>
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                                    Status: <strong style={{ textTransform: 'capitalize' }}>{scanStatus}</strong>
                                </p>
                            </div>
                            <button
                                onClick={cancelScan}
                                style={{
                                    padding: '0.5rem 1rem',
                                    fontSize: '0.85rem',
                                    border: '1px solid #ef4444',
                                    borderRadius: 'var(--radius-md)',
                                    background: 'white',
                                    color: '#ef4444',
                                    cursor: 'pointer',
                                    fontFamily: 'inherit',
                                    fontWeight: 500
                                }}
                            >
                                Cancel Scan
                            </button>
                        </div>

                        {/* Progress Bar */}
                        <div style={{ marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                                <span style={{ fontWeight: 500 }}>Progress: {pagesScanned} / {totalPages || '?'} pages</span>
                                <span style={{ fontWeight: 600, color: 'var(--primary-start)' }}>{progress}%</span>
                            </div>
                            <div style={{ height: '12px', background: '#e2e8f0', borderRadius: '6px', overflow: 'hidden', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)' }}>
                                <div
                                    style={{
                                        height: '100%',
                                        width: `${progress}%`,
                                        background: 'var(--primary-gradient)',
                                        transition: 'width 0.3s ease',
                                        boxShadow: '0 2px 4px rgba(79, 70, 229, 0.3)'
                                    }}
                                />
                            </div>
                        </div>

                        {/* Current URL Being Scanned */}
                        {currentUrl && (
                            <div style={{ background: 'white', padding: '0.75rem', borderRadius: 'var(--radius-md)', fontSize: '0.85rem', border: '1px solid #e0e7ff' }}>
                                <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>Currently scanning:</span>
                                <div style={{ marginTop: '0.25rem', color: 'var(--primary-start)', fontFamily: 'monospace', fontSize: '0.8rem', wordBreak: 'break-all' }}>
                                    {currentUrl}
                                </div>
                            </div>
                        )}
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

            {/* Scanner Selection Modal */}
            {showScannerModal && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowScannerModal(false)}>
                    <div className="card" style={{ width: '600px', maxWidth: '90%', maxHeight: '80vh', overflow: 'auto' }} onClick={(e) => e.stopPropagation()}>
                        <h2 style={{ marginBottom: '0.5rem' }}>Select Scanners</h2>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                            Choose which accessibility scanners to run for this quick scan
                        </p>

                        {/* Quick Actions */}
                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                            <button
                                type="button"
                                onClick={selectRecommended}
                                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}
                            >
                                ✓ Recommended (Fast)
                            </button>
                            <button
                                type="button"
                                onClick={selectAll}
                                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}
                            >
                                Select All
                            </button>
                            <button
                                type="button"
                                onClick={() => setSelectedScanners([])}
                                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}
                            >
                                Clear All
                            </button>
                        </div>

                        {/* Scanner List - Grouped by Category */}
                        <div style={{ marginBottom: '1.5rem', maxHeight: '400px', overflowY: 'auto' }}>
                            {['Core', 'Essential', 'Content', 'Mobile', 'WCAG 2.2', 'Navigation', 'Advanced'].map((category) => {
                                const categoryScannners = ALL_SCANNERS.filter(s => s.category === category);
                                if (categoryScannners.length === 0) return null;

                                return (
                                    <div key={category} style={{ marginBottom: '1rem' }}>
                                        <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                            {category}
                                        </h4>
                                        {categoryScannners.map((scanner) => (
                                            <div
                                                key={scanner.id}
                                                onClick={() => toggleScanner(scanner.id)}
                                                style={{
                                                    padding: '0.75rem',
                                                    border: `2px solid ${selectedScanners.includes(scanner.id) ? 'var(--primary-start)' : 'var(--border-light)'}`,
                                                    borderRadius: 'var(--radius-md)',
                                                    marginBottom: '0.4rem',
                                                    cursor: 'pointer',
                                                    background: selectedScanners.includes(scanner.id) ? 'rgba(79, 70, 229, 0.05)' : 'white',
                                                    transition: 'all 0.2s',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.75rem'
                                                }}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={selectedScanners.includes(scanner.id)}
                                                    onChange={() => {}}
                                                    style={{ cursor: 'pointer' }}
                                                />
                                                <strong style={{ fontSize: '0.85rem', flex: 1 }}>{scanner.name}</strong>
                                            </div>
                                        ))}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Selected Count */}
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                            {selectedScanners.length} scanner{selectedScanners.length !== 1 ? 's' : ''} selected
                        </p>

                        {/* Actions */}
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                            <button
                                type="button"
                                onClick={() => setShowScannerModal(false)}
                                style={{ padding: '0.75rem 1.5rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowScannerModal(false)}
                                className="btn-gradient"
                                style={{ padding: '0.75rem 1.5rem' }}
                            >
                                Apply Scanners
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
