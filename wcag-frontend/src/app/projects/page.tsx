'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast-context';
import { SkeletonProjectCard } from '@/components/Skeleton';
import { Pagination } from '@/components/Pagination';
import type { Project } from '@/lib/types';

// Available scanners with descriptions (matching backend SCANNERS registry)
const AVAILABLE_SCANNERS = [
    // ===== CORE SCANNERS (Recommended for all scans) =====
    {
        id: 'axe',
        name: 'Axe Core',
        description: 'Industry-standard automated accessibility testing engine',
        category: 'Core',
        recommended: true,
        wcag: 'WCAG 2.0, 2.1, 2.2'
    },
    {
        id: 'pa11y',
        name: 'Pa11y',
        description: 'Automated accessibility testing using HTML_CodeSniffer',
        category: 'Core',
        recommended: true,
        wcag: 'WCAG 2.0, 2.1'
    },
    {
        id: 'html_validator',
        name: 'HTML Validator',
        description: 'W3C HTML validation and WCAG compliance checker',
        category: 'Core',
        recommended: true,
        wcag: 'HTML5, WCAG 2.1'
    },

    // ===== ESSENTIAL SCANNERS (High impact) =====
    {
        id: 'contrast',
        name: 'Contrast Checker',
        description: 'Color contrast ratio validation (WCAG 1.4.3, 1.4.6)',
        category: 'Essential',
        recommended: true,
        wcag: '1.4.3 (AA), 1.4.6 (AAA)'
    },
    {
        id: 'keyboard',
        name: 'Keyboard Navigation',
        description: 'Keyboard accessibility and focus management',
        category: 'Essential',
        recommended: true,
        wcag: '2.1.1, 2.1.2, 2.4.7'
    },
    {
        id: 'aria',
        name: 'ARIA Validator',
        description: 'ARIA roles, states, and properties validation',
        category: 'Essential',
        recommended: true,
        wcag: '4.1.2 (Name, Role, Value)'
    },
    {
        id: 'forms',
        name: 'Forms Accessibility',
        description: 'Form labels, error messages, and input validation',
        category: 'Essential',
        recommended: true,
        wcag: '3.3.1, 3.3.2, 4.1.3'
    },

    // ===== CONTENT SCANNERS =====
    {
        id: 'image_alt',
        name: 'Image Alt Text',
        description: 'Alternative text validation for images',
        category: 'Content',
        recommended: false,
        wcag: '1.1.1 (Non-text Content)'
    },
    {
        id: 'link_text',
        name: 'Link Text',
        description: 'Meaningful and descriptive link text checker',
        category: 'Content',
        recommended: false,
        wcag: '2.4.4 (Link Purpose)'
    },
    {
        id: 'readability',
        name: 'Readability',
        description: 'Content readability and reading level analysis',
        category: 'Content',
        recommended: false,
        wcag: '3.1.5 (Reading Level)'
    },
    {
        id: 'media',
        name: 'Media Accessibility',
        description: 'Audio/video captions, transcripts, and controls',
        category: 'Content',
        recommended: false,
        wcag: '1.2.1, 1.2.2, 1.2.3'
    },

    // ===== MOBILE & TOUCH =====
    {
        id: 'touch_target',
        name: 'Touch Target Size',
        description: 'Minimum touch target sizes for mobile (WCAG 2.5.5)',
        category: 'Mobile',
        recommended: false,
        wcag: '2.5.5 (Target Size)'
    },
    {
        id: 'pointer_gestures',
        name: 'Pointer Gestures',
        description: 'Single pointer and dragging alternatives (WCAG 2.2 - 2.5.7)',
        category: 'Mobile',
        recommended: false,
        wcag: '2.5.7 (Dragging Movements)'
    },

    // ===== WCAG 2.2 NEW CRITERIA =====
    {
        id: 'focus_obscured',
        name: 'Focus Not Obscured',
        description: 'Ensure focused elements are not hidden (WCAG 2.2 - 2.4.11, 2.4.12)',
        category: 'WCAG 2.2',
        recommended: false,
        wcag: '2.4.11 (Min), 2.4.12 (Enhanced)'
    },
    {
        id: 'hover_content',
        name: 'Hover/Focus Content',
        description: 'Dismissible and hoverable tooltip content (WCAG 2.2 - 1.4.13)',
        category: 'WCAG 2.2',
        recommended: false,
        wcag: '1.4.13 (Content on Hover/Focus)'
    },
    {
        id: 'character_shortcuts',
        name: 'Character Key Shortcuts',
        description: 'Single character keyboard shortcuts (WCAG 2.1 - 2.1.4)',
        category: 'WCAG 2.2',
        recommended: false,
        wcag: '2.1.4 (Character Key Shortcuts)'
    },

    // ===== NAVIGATION & STRUCTURE =====
    {
        id: 'consistent_navigation',
        name: 'Consistent Navigation',
        description: 'Navigation consistency across pages (WCAG 3.2.3)',
        category: 'Navigation',
        recommended: false,
        wcag: '3.2.3 (Consistent Navigation)'
    },
    {
        id: 'multiple_ways',
        name: 'Multiple Ways',
        description: 'Multiple ways to find pages (WCAG 2.4.5)',
        category: 'Navigation',
        recommended: false,
        wcag: '2.4.5 (Multiple Ways)'
    },
    {
        id: 'interactive',
        name: 'Interactive Elements',
        description: 'Buttons, dropdowns, modals, and widget patterns',
        category: 'Navigation',
        recommended: false,
        wcag: 'Multiple criteria'
    },

    // ===== ADVANCED =====
    {
        id: 'lighthouse',
        name: 'Lighthouse',
        description: 'Google\'s comprehensive web quality audits',
        category: 'Advanced',
        recommended: false,
        wcag: 'Performance + Accessibility'
    },
    {
        id: 'seo',
        name: 'SEO Accessibility',
        description: 'SEO best practices that improve accessibility',
        category: 'Advanced',
        recommended: false,
        wcag: 'Semantic HTML + SEO'
    },
    {
        id: 'color_only',
        name: 'Color Only Information',
        description: 'Detect information conveyed by color alone (WCAG 1.4.1)',
        category: 'Advanced',
        recommended: false,
        wcag: '1.4.1 (Use of Color)'
    },
    {
        id: 'media_accessibility',
        name: 'Advanced Media',
        description: 'Extended media accessibility checks including sign language',
        category: 'Advanced',
        recommended: false,
        wcag: '1.2.6 (Sign Language)'
    },
];

export default function ProjectsPage() {
    const router = useRouter();
    const toast = useToast();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creating, setCreating] = useState(false);
    const [showScannerModal, setShowScannerModal] = useState(false);
    const [selectedProject, setSelectedProject] = useState<string | null>(null);
    const [selectedScanners, setSelectedScanners] = useState<string[]>(['axe', 'pa11y', 'html_validator', 'contrast', 'keyboard', 'aria', 'forms']);
    const [scanning, setScanning] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);
    const itemsPerPage = 12;

    useEffect(() => {
        loadProjects();
    }, []);

    const loadProjects = async (page: number = currentPage) => {
        setLoading(true);
        try {
            const response = await api.getProjects({ page, limit: itemsPerPage });
            setProjects(response.data);
            if (response.pagination) {
                setTotalPages(response.pagination.totalPages);
                setTotalItems(response.pagination.totalItems);
                setCurrentPage(page);
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        } finally {
            setLoading(false);
        }
    };

    const handlePageChange = (page: number) => {
        loadProjects(page);
        window.scrollTo({ top: 0, behavior: 'smooth' });
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
            toast.success(`Project "${data.name}" created successfully!`);
        } catch (error: any) {
            console.error('Failed to create project:', error);
            const errorMessage = error.response?.data?.error?.message || 'Failed to create project';
            toast.error(errorMessage);
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
            toast.warning('Please select at least one scanner');
            return;
        }

        setScanning(true);
        try {
            // Load scan preferences from localStorage
            let scanConfig: any = {
                projectId: selectedProject,
                scanners: selectedScanners
            };

            const savedPrefs = localStorage.getItem('scanPreferences');
            if (savedPrefs) {
                try {
                    const prefs = JSON.parse(savedPrefs);
                    // Only add maxPages and maxDepth if site-wide is enabled
                    if (prefs.siteWide) {
                        scanConfig.maxPages = prefs.maxPages || 10;
                        scanConfig.maxDepth = prefs.maxDepth || 3;
                    }
                } catch (e) {
                    console.error('Failed to parse scan preferences:', e);
                }
            }

            const response = await api.startProjectScan(scanConfig);
            setShowScannerModal(false);
            toast.success('Scan started successfully!');
            router.push(`/scan?scanId=${response.data.scanId}`);
        } catch (error: any) {
            console.error('Failed to start scan:', error);
            const errorMessage = error.response?.data?.error?.message || 'Failed to start scan';
            toast.error(errorMessage);
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
        return (
            <>
                <header className="section-header">
                    <div>
                        <h1 className="section-title">Projects</h1>
                        <p className="section-subtitle">Manage your websites and scan configurations.</p>
                    </div>
                </header>
                <div className="projects-grid">
                    {Array.from({ length: 6 }).map((_, i) => (
                        <SkeletonProjectCard key={i} />
                    ))}
                </div>
            </>
        );
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
                                <button
                                    onClick={() => router.push(`/projects/${project.id}`)}
                                    style={{ padding: '0.5rem 1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit', fontSize: '0.8rem' }}
                                >
                                    Settings
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {!loading && projects.length > 0 && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    totalItems={totalItems}
                    itemsPerPage={itemsPerPage}
                    onPageChange={handlePageChange}
                    loading={loading}
                />
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

                        {/* Scanner List - Grouped by Category */}
                        <div style={{ marginBottom: '1.5rem', maxHeight: '500px', overflowY: 'auto' }}>
                            {['Core', 'Essential', 'Content', 'Mobile', 'WCAG 2.2', 'Navigation', 'Advanced'].map((category) => {
                                const categoryScannners = AVAILABLE_SCANNERS.filter(s => s.category === category);
                                if (categoryScannners.length === 0) return null;

                                return (
                                    <div key={category} style={{ marginBottom: '1.5rem' }}>
                                        <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                            {category}
                                        </h4>
                                        {categoryScannners.map((scanner) => (
                                            <div
                                                key={scanner.id}
                                                onClick={() => toggleScanner(scanner.id)}
                                                style={{
                                                    padding: '0.875rem',
                                                    border: `2px solid ${selectedScanners.includes(scanner.id) ? 'var(--primary-start)' : 'var(--border-light)'}`,
                                                    borderRadius: 'var(--radius-md)',
                                                    marginBottom: '0.5rem',
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
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
                                                            <strong style={{ fontSize: '0.9rem' }}>{scanner.name}</strong>
                                                            {scanner.recommended && (
                                                                <span style={{ fontSize: '0.7rem', background: 'var(--grad-success)', color: 'white', padding: '0.125rem 0.4rem', borderRadius: '0.25rem' }}>
                                                                    Recommended
                                                                </span>
                                                            )}
                                                            <span style={{ fontSize: '0.7rem', background: '#e0e7ff', color: '#4c1d95', padding: '0.125rem 0.4rem', borderRadius: '0.25rem' }}>
                                                                {scanner.wcag}
                                                            </span>
                                                        </div>
                                                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: 0 }}>
                                                            {scanner.description}
                                                        </p>
                                                    </div>
                                                </div>
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

                        {/* Scan Configuration Info */}
                        {(() => {
                            const savedPrefs = localStorage.getItem('scanPreferences');
                            let scanType = 'Site-wide (default)';
                            let details = 'Max 10 pages, depth 3';

                            if (savedPrefs) {
                                try {
                                    const prefs = JSON.parse(savedPrefs);
                                    if (prefs.siteWide) {
                                        scanType = 'Site-wide';
                                        details = `Max ${prefs.maxPages || 10} pages, depth ${prefs.maxDepth || 3}`;
                                    } else {
                                        scanType = 'Single page';
                                        details = 'Main URL only';
                                    }
                                } catch (e) {}
                            }

                            return (
                                <div style={{ background: '#f0f9ff', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', border: '1px solid #bae6fd' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                        <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#0369a1' }}>⚙️ Scan Configuration:</span>
                                        <span style={{ fontSize: '0.9rem', color: '#0369a1' }}>{scanType}</span>
                                    </div>
                                    <p style={{ fontSize: '0.8rem', color: '#0c4a6e', margin: 0 }}>
                                        {details} • <a href="/settings" style={{ color: '#0369a1', textDecoration: 'underline' }}>Change in Settings</a>
                                    </p>
                                </div>
                            );
                        })()}

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
