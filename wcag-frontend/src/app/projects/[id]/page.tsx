'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast-context';
import type { Project } from '@/lib/types';

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
