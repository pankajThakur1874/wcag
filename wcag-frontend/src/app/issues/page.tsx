'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Issue, Report } from '@/lib/types';

export default function IssuesPage() {
    const [reports, setReports] = useState<Report[]>([]);
    const [issues, setIssues] = useState<Issue[]>([]);
    const [selectedScanId, setSelectedScanId] = useState('');
    const [loading, setLoading] = useState(true);
    const [loadingIssues, setLoadingIssues] = useState(false);

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
            const data = response.data;
            if (Array.isArray(data)) {
                setReports(data);
            } else if (data?.items && Array.isArray(data.items)) {
                setReports(data.items);
            } else {
                setReports([]);
            }
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
            const response = await api.getIssues(scanId, { limit: 100 });
            const data = response.data;
            if (Array.isArray(data)) {
                setIssues(data);
            } else if (data?.items && Array.isArray(data.items)) {
                setIssues(data.items);
            } else {
                setIssues([]);
            }
        } catch (error) {
            console.error('Failed to load issues:', error);
            setIssues([]);
        } finally {
            setLoadingIssues(false);
        }
    };

    const handleReportChange = (scanId: string) => {
        setSelectedScanId(scanId);
        loadIssues(scanId);
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
                    {reports.map((report) => (
                        <option key={report.id} value={report.id}>
                            {report.projectName || report.url} — {new Date(report.completedAt).toLocaleDateString()}
                        </option>
                    ))}
                </select>
                <button
                    className="btn-gradient"
                    style={{ background: 'var(--text-secondary)' }}
                    onClick={() => loadIssues(selectedScanId)}
                >
                    Refresh
                </button>
            </div>

            {/* Issues List */}
            <div>
                {loadingIssues ? (
                    <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>Loading issues...</div>
                ) : !selectedScanId ? (
                    <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        Select a scan report above to view its issues.
                    </div>
                ) : issues.length === 0 ? (
                    <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                        No issues found for this scan. 🎉
                    </div>
                ) : (
                    issues.map((issue) => (
                        <div key={issue.id} className={`card issue-card ${impactColor[issue.impact] || ''}`}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                                <h4 style={{ fontWeight: 600, flex: 1 }}>{issue.description}</h4>
                                <span className={`status-pill ${issue.impact === 'critical' ? 'status-danger' : issue.impact === 'serious' ? 'status-warning' : 'status-success'}`}>
                                    {issue.impact}
                                </span>
                            </div>
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                WCAG: {issue.wcagCriteria} • Element: <code style={{ background: '#f1f5f9', padding: '0.15rem 0.4rem', borderRadius: '4px', fontSize: '0.8rem' }}>{issue.selector}</code>
                            </p>
                            {issue.howToFix && (
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                    <strong>Fix:</strong> {issue.howToFix}
                                </p>
                            )}
                        </div>
                    ))
                )}
            </div>
        </>
    );
}
