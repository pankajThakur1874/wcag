'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/lib/toast-context';
import { SkeletonIssueCard } from '@/components/Skeleton';
import type { Issue, Report, ImpactLevel, IssueStatus } from '@/lib/types';

export default function IssuesPage() {
    const toast = useToast();
    const [reports, setReports] = useState<Report[]>([]);
    const [issues, setIssues] = useState<Issue[]>([]);
    const [selectedScanId, setSelectedScanId] = useState('');
    const [loading, setLoading] = useState(true);
    const [loadingIssues, setLoadingIssues] = useState(false);
    const [filterImpact, setFilterImpact] = useState<string>('all');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [updatingIssues, setUpdatingIssues] = useState<Set<string>>(new Set());

    const impactColor: Record<string, string> = {
        critical: 'impact-critical',
        serious: 'impact-serious',
        moderate: 'impact-moderate',
        minor: 'impact-minor',
    };

    useEffect(() => {
        loadReports();
    }, []);

    const loadReports = async () => {
        try {
            const response = await api.getReports({ limit: 100 });
            setReports(response.data);
        } catch (error) {
            console.error('Failed to load reports:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadIssues = async (scanId: string) => {
        if (!scanId) { setIssues([]); return; }
        setLoadingIssues(true);
        try {
            const params: any = { limit: 100 }; // Backend max limit is 100
            if (filterImpact !== 'all') {
                params.impact = filterImpact;
            }
            if (filterStatus !== 'all') {
                params.status = filterStatus;
            }
            const response = await api.getIssues(scanId, params);
            setIssues(response.data);
        } catch (error) {
            console.error('Failed to load issues:', error);
            setIssues([]);
        } finally {
            setLoadingIssues(false);
        }
    };

    // Reload issues when filters change
    useEffect(() => {
        if (selectedScanId) {
            loadIssues(selectedScanId);
        }
    }, [filterImpact, filterStatus]);

    const handleReportChange = (scanId: string) => {
        setSelectedScanId(scanId);
        loadIssues(scanId);
    };

    const updateIssueStatus = async (issueId: string, newStatus: IssueStatus) => {
        setUpdatingIssues(prev => new Set(prev).add(issueId));
        try {
            await api.updateIssue(issueId, { status: newStatus });

            // Update the issue in the local state
            setIssues(prev =>
                prev.map(issue =>
                    issue.id === issueId
                        ? { ...issue, status: newStatus }
                        : issue
                )
            );

            toast.success(`Issue marked as ${newStatus}`);
        } catch (error: any) {
            console.error('Failed to update issue:', error);
            const errorMessage = error.response?.data?.error?.message || 'Failed to update issue';
            toast.error(errorMessage);
        } finally {
            setUpdatingIssues(prev => {
                const newSet = new Set(prev);
                newSet.delete(issueId);
                return newSet;
            });
        }
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <>
            <header className="section-header">
                <h1 className="section-title">Issues</h1>
                <p className="section-subtitle">Review detected accessibility violations.</p>
            </header>

            {/* Report Selector */}
            <div className="report-controls">
                <label style={{ fontWeight: 600 }}>Select Report:</label>
                <select
                    className="form-select"
                    style={{ margin: 0, maxWidth: '400px' }}
                    value={selectedScanId}
                    onChange={(e) => handleReportChange(e.target.value)}
                >
                    <option value="">-- Choose a Scan Report --</option>
                    {reports.map((report) => {
                        const dateStr = report.completedAt
                            ? new Date(report.completedAt).toLocaleDateString()
                            : 'Date N/A';
                        return (
                            <option key={report.id} value={report.id}>
                                {report.projectName || report.url} — {dateStr}
                            </option>
                        );
                    })}
                </select>
                <button
                    className="btn-gradient"
                    style={{ background: 'var(--text-secondary)' }}
                    onClick={() => loadIssues(selectedScanId)}
                >
                    Refresh
                </button>
            </div>

            {/* Filters */}
            {selectedScanId && (
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <label style={{ fontWeight: 500, fontSize: '0.9rem' }}>Impact:</label>
                        <select
                            className="form-select"
                            style={{ margin: 0, width: '150px' }}
                            value={filterImpact}
                            onChange={(e) => setFilterImpact(e.target.value)}
                        >
                            <option value="all">All Levels</option>
                            <option value="critical">Critical</option>
                            <option value="serious">Serious</option>
                            <option value="moderate">Moderate</option>
                            <option value="minor">Minor</option>
                        </select>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <label style={{ fontWeight: 500, fontSize: '0.9rem' }}>Status:</label>
                        <select
                            className="form-select"
                            style={{ margin: 0, width: '150px' }}
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                        >
                            <option value="all">All Statuses</option>
                            <option value="open">Open</option>
                            <option value="fixed">Fixed</option>
                            <option value="ignored">Ignored</option>
                        </select>
                    </div>

                    {(filterImpact !== 'all' || filterStatus !== 'all') && (
                        <button
                            onClick={() => {
                                setFilterImpact('all');
                                setFilterStatus('all');
                            }}
                            style={{
                                padding: '0.5rem 1rem',
                                fontSize: '0.85rem',
                                border: '1px solid var(--border-light)',
                                borderRadius: 'var(--radius-md)',
                                background: 'white',
                                cursor: 'pointer',
                                fontFamily: 'inherit'
                            }}
                        >
                            Clear Filters
                        </button>
                    )}

                    <div style={{ marginLeft: 'auto', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                        Showing {issues.length} issue{issues.length !== 1 ? 's' : ''}
                    </div>
                </div>
            )}

            {/* Issues List */}
            <div>
                {loadingIssues ? (
                    <>
                        {Array.from({ length: 5 }).map((_, i) => (
                            <SkeletonIssueCard key={i} />
                        ))}
                    </>
                ) : !selectedScanId ? (
                    <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        Select a scan report above to view its issues.
                    </div>
                ) : issues.length === 0 ? (
                    <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        No issues found for this scan. 🎉
                    </div>
                ) : (
                    issues.map((issue) => {
                        const isUpdating = updatingIssues.has(issue.id);
                        return (
                            <div key={issue.id} className={`card issue-card ${impactColor[issue.impact] || ''}`}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem', gap: '1rem' }}>
                                    <h4 style={{ fontWeight: 600, flex: 1 }}>{issue.description}</h4>
                                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                        <span className={`status-pill ${issue.impact === 'critical' ? 'status-danger' : issue.impact === 'serious' ? 'status-warning' : 'status-success'}`}>
                                            {issue.impact}
                                        </span>
                                        <span className={`status-pill ${issue.status === 'open' ? 'status-warning' : issue.status === 'fixed' ? 'status-success' : ''}`} style={{ textTransform: 'capitalize' }}>
                                            {issue.status}
                                        </span>
                                    </div>
                                </div>
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                    WCAG: {issue.wcagCriteria} • Element: <code style={{ background: '#f1f5f9', padding: '0.15rem 0.4rem', borderRadius: '4px', fontSize: '0.8rem' }}>{issue.selector}</code>
                                </p>
                                {issue.howToFix && (
                                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                                        <strong>Fix:</strong> {issue.howToFix}
                                    </p>
                                )}
                                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                                    {issue.status !== 'fixed' && (
                                        <button
                                            onClick={() => updateIssueStatus(issue.id, 'fixed')}
                                            disabled={isUpdating}
                                            style={{
                                                padding: '0.4rem 0.8rem',
                                                fontSize: '0.8rem',
                                                border: '1px solid #10b981',
                                                borderRadius: 'var(--radius-md)',
                                                background: 'white',
                                                color: '#10b981',
                                                cursor: isUpdating ? 'not-allowed' : 'pointer',
                                                fontFamily: 'inherit',
                                                fontWeight: 500,
                                                opacity: isUpdating ? 0.6 : 1
                                            }}
                                        >
                                            {isUpdating ? 'Updating...' : '✓ Mark as Fixed'}
                                        </button>
                                    )}
                                    {issue.status !== 'ignored' && (
                                        <button
                                            onClick={() => updateIssueStatus(issue.id, 'ignored')}
                                            disabled={isUpdating}
                                            style={{
                                                padding: '0.4rem 0.8rem',
                                                fontSize: '0.8rem',
                                                border: '1px solid #6b7280',
                                                borderRadius: 'var(--radius-md)',
                                                background: 'white',
                                                color: '#6b7280',
                                                cursor: isUpdating ? 'not-allowed' : 'pointer',
                                                fontFamily: 'inherit',
                                                fontWeight: 500,
                                                opacity: isUpdating ? 0.6 : 1
                                            }}
                                        >
                                            {isUpdating ? 'Updating...' : '✕ Mark as Ignored'}
                                        </button>
                                    )}
                                    {issue.status !== 'open' && (
                                        <button
                                            onClick={() => updateIssueStatus(issue.id, 'open')}
                                            disabled={isUpdating}
                                            style={{
                                                padding: '0.4rem 0.8rem',
                                                fontSize: '0.8rem',
                                                border: '1px solid #f59e0b',
                                                borderRadius: 'var(--radius-md)',
                                                background: 'white',
                                                color: '#f59e0b',
                                                cursor: isUpdating ? 'not-allowed' : 'pointer',
                                                fontFamily: 'inherit',
                                                fontWeight: 500,
                                                opacity: isUpdating ? 0.6 : 1
                                            }}
                                        >
                                            {isUpdating ? 'Updating...' : '↺ Reopen'}
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </>
    );
}
