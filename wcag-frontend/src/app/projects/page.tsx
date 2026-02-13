'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { Project } from '@/lib/types';

// Available scanners with descriptions (matching backend SCANNERS registry)
const AVAILABLE_SCANNERS = [
    // Core scanners (recommended for comprehensive testing)
    { id: 'axe', name: 'Axe Core', description: 'Industry-standard accessibility testing', recommended: true },
    { id: 'pa11y', name: 'Pa11y', description: 'Automated accessibility testing tool', recommended: true },
    { id: 'html_validator', name: 'HTML Validator', description: 'HTML/WCAG compliance checker', recommended: true },

    // Additional scanners
    { id: 'contrast', name: 'Contrast Checker', description: 'Color contrast validation', recommended: false },
    { id: 'keyboard', name: 'Keyboard Scanner', description: 'Keyboard navigation testing', recommended: false },
    { id: 'aria', name: 'ARIA Scanner', description: 'ARIA attributes validation', recommended: false },
    { id: 'forms', name: 'Forms Scanner', description: 'Form accessibility checks', recommended: false },
    { id: 'lighthouse', name: 'Lighthouse', description: 'Google\'s web quality tool', recommended: false },
    { id: 'image_alt', name: 'Image Alt Text', description: 'Image alternative text validation', recommended: false },
    { id: 'link_text', name: 'Link Text', description: 'Meaningful link text checker', recommended: false },
    { id: 'readability', name: 'Readability', description: 'Content readability analysis', recommended: false },
    { id: 'media', name: 'Media Scanner', description: 'Audio/video accessibility', recommended: false },

    // WCAG 2.2 Advanced scanners
    { id: 'focus_obscured', name: 'Focus Visible (2.4.12)', description: 'WCAG 2.2 Level AA - Focus not obscured', recommended: false },
    { id: 'hover_content', name: 'Hover Content (1.4.13)', description: 'WCAG 2.2 Level AA - Dismissible hover content', recommended: false },
    { id: 'pointer_gestures', name: 'Pointer Gestures (2.5.7)', description: 'WCAG 2.2 Level A - Dragging movements', recommended: false },
];

export default function ProjectsPage() {
    const router = useRouter();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creating, setCreating] = useState(false);
    const [showScannerModal, setShowScannerModal] = useState(false);
    const [selectedProject, setSelectedProject] = useState<string | null>(null);
    const [selectedScanners, setSelectedScanners] = useState<string[]>(['axe', 'pa11y', 'html_validator']);
    const [scanning, setScanning] = useState(false);

    useEffect(() => {
        loadProjects();
    }, []);

    const loadProjects = async () => {
        try {
            const response = await api.getProjects({ limit: 100 });
            // Handle both paginated ({items: [...]}) and direct array responses
            const data = response.data;
            if (Array.isArray(data)) {
                setProjects(data);
            } else if (data?.items && Array.isArray(data.items)) {
                setProjects(data.items);
            } else {
                setProjects([]);
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProject = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);

        try {
            const formData = new FormData(e.target as HTMLFormElement);
            const data = {
                name: formData.get('name') as string,
                url: formData.get('url') as string,
                description: formData.get('description') as string || undefined,
            };

            await api.createProject(data);
            setShowCreateModal(false);
            await loadProjects();
        } catch (error) {
            console.error('Failed to create project:', error);
            alert('Failed to create project');
        } finally {
            setCreating(false);
        }
    };

    const handleScanProject = (projectId: string) => {
        setSelectedProject(projectId);
        setShowScannerModal(true);
    };

    const handleStartScan = async () => {
        if (!selectedProject || selectedScanners.length === 0) {
            alert('Please select at least one scanner');
            return;
        }

        setScanning(true);
        try {
            const response = await api.startProjectScan({
                projectId: selectedProject,
                scanners: selectedScanners
            });
            setShowScannerModal(false);
            router.push(`/scan?scanId=${response.data.scanId}`);
        } catch (error) {
            console.error('Failed to start scan:', error);
            alert('Failed to start scan');
        } finally {
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
        const recommended = AVAILABLE_SCANNERS.filter(s => s.recommended).map(s => s.id);
        setSelectedScanners(recommended);
    };

    const selectAll = () => {
        setSelectedScanners(AVAILABLE_SCANNERS.map(s => s.id));
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <>
            <header className="section-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                    <h1 className="section-title">Projects</h1>
                    <p className="section-subtitle">Manage your websites and scan configurations.</p>
                </div>
                <button className="btn-gradient" onClick={() => setShowCreateModal(true)}>+ New Project</button>
            </header>

            {projects.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>No projects yet</p>
                    <button className="btn-gradient" onClick={() => setShowCreateModal(true)}>Create Your First Project</button>
                </div>
            ) : (
                <div className="projects-grid">
                    {projects.map((project) => (
                        <div key={project.id} className="card project-card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                <h3 style={{ fontWeight: 600 }}>{project.name}</h3>
                                <span className={`status-pill ${project.status === 'active' ? 'status-success' : 'status-warning'}`}>
                                    {project.status}
                                </span>
                            </div>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>{project.url}</p>
                            {project.description && (
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>{project.description}</p>
                            )}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
                                <span>Last scan: {project.lastScan ? new Date(project.lastScan).toLocaleDateString() : 'Never'}</span>
                                {project.score !== undefined && (
                                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>Score: {project.score}%</span>
                                )}
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
                                <button
                                    className="btn-gradient"
                                    style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}
                                    onClick={() => handleScanProject(project.id)}
                                >
                                    Scan Now
                                </button>
                                <button style={{ padding: '0.5rem 1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit', fontSize: '0.8rem' }}>
                                    Settings
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create Project Modal */}
            {showCreateModal && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowCreateModal(false)}>
                    <div className="card" style={{ width: '500px', maxWidth: '90%' }} onClick={(e) => e.stopPropagation()}>
                        <h2 style={{ marginBottom: '1.5rem' }}>Create New Project</h2>
                        <form onSubmit={handleCreateProject}>
                            <div style={{ marginBottom: '1rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>Project Name</label>
                                <input
                                    type="text"
                                    name="name"
                                    required
                                    placeholder="My Website"
                                    style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontFamily: 'inherit' }}
                                />
                            </div>
                            <div style={{ marginBottom: '1rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>Website URL</label>
                                <input
                                    type="url"
                                    name="url"
                                    required
                                    placeholder="https://example.com"
                                    style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontFamily: 'inherit' }}
                                />
                            </div>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>Description (Optional)</label>
                                <textarea
                                    name="description"
                                    placeholder="Brief description of the project"
                                    rows={3}
                                    style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontFamily: 'inherit', resize: 'vertical' }}
                                />
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    style={{ padding: '0.75rem 1.5rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn-gradient"
                                    style={{ padding: '0.75rem 1.5rem' }}
                                    disabled={creating}
                                >
                                    {creating ? 'Creating...' : 'Create Project'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Scanner Selection Modal */}
            {showScannerModal && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowScannerModal(false)}>
                    <div className="card" style={{ width: '600px', maxWidth: '90%', maxHeight: '80vh', overflow: 'auto' }} onClick={(e) => e.stopPropagation()}>
                        <h2 style={{ marginBottom: '0.5rem' }}>Select Scanners</h2>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                            Choose which accessibility scanners to run for this project
                        </p>

                        {/* Quick Actions */}
                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                            <button
                                type="button"
                                onClick={selectRecommended}
                                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}
                            >
                                ✓ Recommended
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

                        {/* Scanner List */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            {AVAILABLE_SCANNERS.map((scanner) => (
                                <div
                                    key={scanner.id}
                                    onClick={() => toggleScanner(scanner.id)}
                                    style={{
                                        padding: '1rem',
                                        border: `2px solid ${selectedScanners.includes(scanner.id) ? 'var(--primary-start)' : 'var(--border-light)'}`,
                                        borderRadius: 'var(--radius-md)',
                                        marginBottom: '0.75rem',
                                        cursor: 'pointer',
                                        background: selectedScanners.includes(scanner.id) ? 'rgba(79, 70, 229, 0.05)' : 'white',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'start', gap: '0.75rem' }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedScanners.includes(scanner.id)}
                                            onChange={() => {}}
                                            style={{ marginTop: '0.25rem', cursor: 'pointer' }}
                                        />
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                                <strong style={{ fontSize: '0.95rem' }}>{scanner.name}</strong>
                                                {scanner.recommended && (
                                                    <span style={{ fontSize: '0.75rem', background: 'var(--grad-success)', color: 'white', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>
                                                        Recommended
                                                    </span>
                                                )}
                                            </div>
                                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0 }}>
                                                {scanner.description}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
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
                                onClick={handleStartScan}
                                className="btn-gradient"
                                style={{ padding: '0.75rem 1.5rem' }}
                                disabled={scanning || selectedScanners.length === 0}
                            >
                                {scanning ? 'Starting Scan...' : `Start Scan with ${selectedScanners.length} Scanner${selectedScanners.length !== 1 ? 's' : ''}`}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
