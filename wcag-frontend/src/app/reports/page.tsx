'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Report } from '@/lib/types';

export default function ReportsPage() {
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadReports();
    }, []);

    const loadReports = async () => {
        try {
            const response = await api.getReports({ limit: 50 });
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

    const handleDownload = async (scanId: string, format: 'html' | 'json' | 'csv') => {
        try {
            const blob = await api.downloadReport(scanId, format);
            api.downloadReportAsFile(blob, `report_${scanId}.${format}`);
        } catch (error) {
            console.error('Failed to download report:', error);
            alert('Failed to download report');
        }
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <>
            <header className="section-header">
                <h1 className="section-title">Reports</h1>
                <p className="section-subtitle">View and download historical scan reports.</p>
            </header>

            <div className="card">
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Project / URL</th>
                                <th>Score</th>
                                <th>Issues</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reports.length === 0 ? (
                                <tr>
                                    <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                                        No completed scans yet. Run a scan to generate reports.
                                    </td>
                                </tr>
                            ) : (
                                reports.map((report) => (
                                    <tr key={report.id}>
                                        <td>{new Date(report.completedAt).toLocaleDateString()}</td>
                                        <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {report.projectName || report.url}
                                        </td>
                                        <td>{report.score}%</td>
                                        <td>{report.issuesCount}</td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                                <button className="btn-gradient" style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem' }} onClick={() => handleDownload(report.id, 'html')}>HTML</button>
                                                <button style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }} onClick={() => handleDownload(report.id, 'json')}>JSON</button>
                                                <button style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }} onClick={() => handleDownload(report.id, 'csv')}>CSV</button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
