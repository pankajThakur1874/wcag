'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { Project } from '@/lib/types';

export default function ProjectsPage() {
    const router = useRouter();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [creating, setCreating] = useState(false);

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

    const handleScanProject = async (projectId: string) => {
        try {
            const response = await api.startProjectScan({ projectId });
            router.push(`/scan?scanId=${response.data.scanId}`);
        } catch (error) {
            console.error('Failed to start scan:', error);
            alert('Failed to start scan');
        }
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
        </>
    );
}
