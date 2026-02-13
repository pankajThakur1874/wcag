'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast-context';
import type { Project } from '@/lib/types';

// Recommended scanners
const RECOMMENDED_SCANNERS = ['axe', 'html_validator', 'contrast', 'keyboard', 'aria'];

// All available scanners (simplified list)
const ALL_SCANNERS = [
    { id: 'axe', name: 'Axe Core', category: 'Core' },
    { id: 'pa11y', name: 'Pa11y', category: 'Core' },
    { id: 'html_validator', name: 'HTML Validator', category: 'Core' },
    { id: 'contrast', name: 'Contrast Checker', category: 'Essential' },
    { id: 'keyboard', name: 'Keyboard Navigation', category: 'Essential' },
    { id: 'aria', name: 'ARIA Validator', category: 'Essential' },
];

export default function ProjectSettingsPage() {
    const params = useParams();
    const router = useRouter();
    const toast = useToast();
    const projectId = params.id as string;

    const [project, setProject] = useState<Project | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    // Form state
    const [name, setName] = useState('');
    const [url, setUrl] = useState('');
    const [description, setDescription] = useState('');
    const [status, setStatus] = useState<'active' | 'archived'>('active');

    // Scan state
    const [scanning, setScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [scanStatus, setScanStatus] = useState('');
    const [scanResult, setScanResult] = useState<{ score?: number; issuesCount?: number } | null>(null);
    const [selectedScanners, setSelectedScanners] = useState<string[]>(RECOMMENDED_SCANNERS);
    const [showScannerModal, setShowScannerModal] = useState(false);
    const [siteWide, setSiteWide] = useState(true);
    const [maxPages, setMaxPages] = useState(10);
    const [maxDepth, setMaxDepth] = useState(3);
    const [currentUrl, setCurrentUrl] = useState<string | null>(null);
    const [pagesScanned, setPagesScanned] = useState(0);
    const [totalPages, setTotalPages] = useState(0);

    useEffect(() => {
        loadProject();
    }, [projectId]);

    const loadProject = async () => {
        try {
            const response = await api.getProject(projectId);
            const proj = response.data;
            setProject(proj);
            setName(proj.name);
            setUrl(proj.url);
            setDescription(proj.description || '');
            setStatus(proj.status);
        } catch (error: any) {
            console.error('Failed to load project:', error);
            toast.error('Failed to load project');
            router.push('/projects');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);

        try {
            await api.updateProject(projectId, {
                name,
                url,
                description,
                status
            });
            toast.success('Project updated successfully!');
            await loadProject();
        } catch (error: any) {
            console.error('Failed to update project:', error);
            const errorMessage = error.response?.data?.error?.message || 'Failed to update project';
            toast.error(errorMessage);
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        setDeleting(true);
        try {
            await api.deleteProject(projectId);
            toast.success('Project deleted successfully');
            router.push('/projects');
        } catch (error: any) {
            console.error('Failed to delete project:', error);
            const errorMessage = error.response?.data?.error?.message || 'Failed to delete project';
            toast.error(errorMessage);
            setDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    const pollScanStatus = useCallback(async (scanId: string) => {
        const poll = async () => {
            try {
                const response = await api.getScanStatus(scanId);
                const data = response.data;

                const pct = data.progress?.percentage ?? 0;
                setScanProgress(pct);
                setScanStatus(data.status);

                if (data.progress) {
                    setCurrentUrl(data.progress.currentUrl || null);
                    setPagesScanned(data.progress.pagesScanned || 0);
                    setTotalPages(data.progress.totalPages || 0);
                }

                if (data.status === 'completed') {
                    setScanProgress(100);
                    setScanResult({ score: data.score, issuesCount: data.issuesCount });
                    setScanning(false);
                    setCurrentUrl(null);
                    toast.success('Scan completed successfully!');
                    return;
                }

                if (data.status === 'failed') {
                    setScanning(false);
                    setCurrentUrl(null);
                    toast.error('Scan failed');
                    return;
                }

                setTimeout(poll, 2000);
            } catch (err) {
                console.error('Poll error:', err);
                setScanning(false);
                setCurrentUrl(null);
                toast.error('Lost connection to scan');
            }
        };

        poll();
    }, [toast]);

    const startScan = async () => {
        if (selectedScanners.length === 0) {
            toast.error('Please select at least one scanner');
            return;
        }

        setScanResult(null);
        setScanning(true);
        setScanProgress(0);
        setScanStatus('queued');

        try {
            const response = await api.startProjectScan({
                projectId,
                scanners: selectedScanners,
                maxPages: siteWide ? maxPages : undefined,
                maxDepth: siteWide ? maxDepth : undefined
            });
            pollScanStatus(response.data.scanId);
            toast.info('Scan started!');
        } catch (err: any) {
            const errorMessage = err.response?.data?.error?.message || 'Failed to start scan';
            toast.error(errorMessage);
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

    if (loading) {
        return <div>Loading project settings...</div>;
    }

    if (!project) {
        return <div>Project not found</div>;
    }

    return (
        <>
            <header className="section-header">
                <div>
                    <h1 className="section-title">Project Settings</h1>
                    <p className="section-subtitle">Configure your project details and settings.</p>
                </div>
                <button
                    onClick={() => router.push('/projects')}
                    style={{
                        padding: '0.6rem 1.2rem',
                        border: '1px solid var(--border-light)',
                        borderRadius: 'var(--radius-md)',
                        background: 'white',
                        cursor: 'pointer',
                        fontFamily: 'inherit'
                    }}
                >
                    ← Back to Projects
                </button>
            </header>

            <div className="card" style={{ maxWidth: '800px' }}>
                <h2 style={{ marginBottom: '1.5rem', fontSize: '1.3rem' }}>Project Information</h2>

                <form onSubmit={handleSave}>
                    {/* Project Name */}
                    <div style={{ marginBottom: '1.25rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                            Project Name <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                border: '1px solid var(--border-light)',
                                borderRadius: 'var(--radius-md)',
                                fontFamily: 'inherit',
                                fontSize: '0.95rem'
                            }}
                        />
                    </div>

                    {/* Website URL */}
                    <div style={{ marginBottom: '1.25rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                            Website URL <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <input
                            type="url"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            required
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                border: '1px solid var(--border-light)',
                                borderRadius: 'var(--radius-md)',
                                fontFamily: 'inherit',
                                fontSize: '0.95rem'
                            }}
                        />
                    </div>

                    {/* Description */}
                    <div style={{ marginBottom: '1.25rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                            Description
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={4}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                border: '1px solid var(--border-light)',
                                borderRadius: 'var(--radius-md)',
                                fontFamily: 'inherit',
                                fontSize: '0.95rem',
                                resize: 'vertical'
                            }}
                        />
                    </div>

                    {/* Status */}
                    <div style={{ marginBottom: '2rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                            Project Status
                        </label>
                        <select
                            value={status}
                            onChange={(e) => setStatus(e.target.value as 'active' | 'archived')}
                            className="form-select"
                            style={{ margin: 0, maxWidth: '200px' }}
                        >
                            <option value="active">Active</option>
                            <option value="archived">Archived</option>
                        </select>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                            Archived projects won't appear in the active projects list
                        </p>
                    </div>

                    {/* Save Button */}
                    <button
                        type="submit"
                        className="btn-gradient"
                        disabled={saving}
                        style={{ padding: '0.75rem 2rem' }}
                    >
                        {saving ? 'Saving Changes...' : 'Save Changes'}
                    </button>
                </form>
            </div>

            {/* Quick Scan Section */}
            <div className="card" style={{ maxWidth: '800px', marginTop: '2rem' }}>
                <h2 style={{ marginBottom: '1rem', fontSize: '1.3rem' }}>Quick Scan</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                    Run an accessibility scan for this project
                </p>

                {/* Scan Type Selection */}
                <div style={{ marginBottom: '1.5rem', padding: '1rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                    <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: 500 }}>Scan Type</label>
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: siteWide ? '1rem' : '0' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <input
                                type="radio"
                                checked={!siteWide}
                                onChange={() => setSiteWide(false)}
                                style={{ cursor: 'pointer' }}
                                disabled={scanning}
                            />
                            <span>
                                <strong>Single Page</strong>
                                <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Scan only the main URL</span>
                            </span>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <input
                                type="radio"
                                checked={siteWide}
                                onChange={() => setSiteWide(true)}
                                style={{ cursor: 'pointer' }}
                                disabled={scanning}
                            />
                            <span>
                                <strong>Site-wide</strong>
                                <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Crawl multiple pages</span>
                            </span>
                        </label>
                    </div>

                    {siteWide && (
                        <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-light)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 500 }}>Max Pages</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="100"
                                    value={maxPages}
                                    onChange={(e) => setMaxPages(parseInt(e.target.value) || 10)}
                                    disabled={scanning}
                                    style={{ width: '100%', padding: '0.5rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontFamily: 'inherit' }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 500 }}>Max Depth</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="10"
                                    value={maxDepth}
                                    onChange={(e) => setMaxDepth(parseInt(e.target.value) || 3)}
                                    disabled={scanning}
                                    style={{ width: '100%', padding: '0.5rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontFamily: 'inherit' }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Scanner Selection */}
                <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <label style={{ fontWeight: 500 }}>Scanners ({selectedScanners.length} selected)</label>
                        <button
                            type="button"
                            onClick={() => setShowScannerModal(true)}
                            disabled={scanning}
                            style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: scanning ? 'not-allowed' : 'pointer', fontFamily: 'inherit', opacity: scanning ? 0.6 : 1 }}
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
                    </div>
                </div>

                {/* Scan Button */}
                <button
                    onClick={startScan}
                    disabled={scanning}
                    className="btn-gradient"
                    style={{ padding: '0.75rem 2rem', opacity: scanning ? 0.6 : 1, cursor: scanning ? 'not-allowed' : 'pointer' }}
                >
                    {scanning ? 'Scanning...' : '🚀 Start Scan'}
                </button>

                {/* Scan Progress */}
                {scanning && (
                    <div style={{ marginTop: '1.5rem', background: 'linear-gradient(135deg, #f8fafc, #e0e7ff)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid #e0e7ff' }}>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-main)' }}>
                            {scanStatus === 'completed' ? '✓ Scan Complete!' : '🔍 Scanning...'}
                        </h3>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                            Status: <strong style={{ textTransform: 'capitalize' }}>{scanStatus}</strong>
                        </p>

                        <div style={{ marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                                <span>Progress: {pagesScanned} / {totalPages || '?'} pages</span>
                                <span style={{ fontWeight: 600, color: 'var(--primary-start)' }}>{scanProgress}%</span>
                            </div>
                            <div style={{ height: '12px', background: '#e2e8f0', borderRadius: '6px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${scanProgress}%`, background: 'var(--primary-gradient)', transition: 'width 0.3s ease' }} />
                            </div>
                        </div>

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

                {/* Scan Results */}
                {scanResult && (
                    <div style={{ marginTop: '1.5rem', padding: '1.5rem', background: '#ecfdf5', borderRadius: 'var(--radius-md)', border: '1px solid #a7f3d0' }}>
                        <h3 style={{ color: '#065f46', marginBottom: '0.5rem' }}>✅ Scan Complete!</h3>
                        <p style={{ color: '#047857', marginBottom: '1rem' }}>
                            Score: <strong>{scanResult.score ?? '–'}%</strong> • Issues: <strong>{scanResult.issuesCount ?? 0}</strong>
                        </p>
                        <button
                            onClick={() => router.push('/issues')}
                            className="btn-gradient"
                            style={{ padding: '0.5rem 1.5rem', fontSize: '0.9rem' }}
                        >
                            View Issues
                        </button>
                    </div>
                )}
            </div>

            {/* Scanner Modal */}
            {showScannerModal && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowScannerModal(false)}>
                    <div className="card" style={{ width: '500px', maxWidth: '90%', maxHeight: '70vh', overflow: 'auto' }} onClick={(e) => e.stopPropagation()}>
                        <h2 style={{ marginBottom: '1rem' }}>Select Scanners</h2>
                        <div style={{ marginBottom: '1.5rem' }}>
                            {ALL_SCANNERS.map((scanner) => (
                                <div
                                    key={scanner.id}
                                    onClick={() => toggleScanner(scanner.id)}
                                    style={{
                                        padding: '0.75rem',
                                        border: `2px solid ${selectedScanners.includes(scanner.id) ? 'var(--primary-start)' : 'var(--border-light)'}`,
                                        borderRadius: 'var(--radius-md)',
                                        marginBottom: '0.5rem',
                                        cursor: 'pointer',
                                        background: selectedScanners.includes(scanner.id) ? 'rgba(79, 70, 229, 0.05)' : 'white',
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
                                    <strong style={{ fontSize: '0.9rem' }}>{scanner.name}</strong>
                                </div>
                            ))}
                        </div>
                        <button
                            onClick={() => setShowScannerModal(false)}
                            className="btn-gradient"
                            style={{ width: '100%', padding: '0.75rem' }}
                        >
                            Apply
                        </button>
                    </div>
                </div>
            )}

            {/* Danger Zone */}
            <div className="card" style={{ maxWidth: '800px', marginTop: '2rem', borderColor: '#fee2e2' }}>
                <h2 style={{ marginBottom: '1rem', fontSize: '1.3rem', color: '#ef4444' }}>Danger Zone</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                    Once you delete a project, there is no going back. All scans and issues associated with this project will be permanently deleted.
                </p>

                {!showDeleteConfirm ? (
                    <button
                        onClick={() => setShowDeleteConfirm(true)}
                        style={{
                            padding: '0.75rem 1.5rem',
                            border: '2px solid #ef4444',
                            borderRadius: 'var(--radius-md)',
                            background: 'white',
                            color: '#ef4444',
                            cursor: 'pointer',
                            fontFamily: 'inherit',
                            fontWeight: 600,
                            fontSize: '0.9rem'
                        }}
                    >
                        Delete Project
                    </button>
                ) : (
                    <div style={{ background: '#fef2f2', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid #fee2e2' }}>
                        <p style={{ fontWeight: 600, marginBottom: '1rem', color: '#991b1b' }}>
                            ⚠️ Are you absolutely sure?
                        </p>
                        <p style={{ fontSize: '0.9rem', color: '#991b1b', marginBottom: '1rem' }}>
                            This action cannot be undone. This will permanently delete the project "{project.name}" and all associated data.
                        </p>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button
                                onClick={handleDelete}
                                disabled={deleting}
                                style={{
                                    padding: '0.75rem 1.5rem',
                                    border: 'none',
                                    borderRadius: 'var(--radius-md)',
                                    background: '#ef4444',
                                    color: 'white',
                                    cursor: deleting ? 'not-allowed' : 'pointer',
                                    fontFamily: 'inherit',
                                    fontWeight: 600,
                                    fontSize: '0.9rem',
                                    opacity: deleting ? 0.6 : 1
                                }}
                            >
                                {deleting ? 'Deleting...' : 'Yes, Delete Forever'}
                            </button>
                            <button
                                onClick={() => setShowDeleteConfirm(false)}
                                disabled={deleting}
                                style={{
                                    padding: '0.75rem 1.5rem',
                                    border: '1px solid var(--border-light)',
                                    borderRadius: 'var(--radius-md)',
                                    background: 'white',
                                    cursor: deleting ? 'not-allowed' : 'pointer',
                                    fontFamily: 'inherit',
                                    fontSize: '0.9rem'
                                }}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
