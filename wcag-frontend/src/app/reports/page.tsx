'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { SkeletonTable } from '@/components/Skeleton';
import { Pagination } from '@/components/Pagination';
import type { Report } from '@/lib/types';

export default function ReportsPage() {
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);
    const [previewReport, setPreviewReport] = useState<string | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);
    const itemsPerPage = 20;

    useEffect(() => {
        loadReports();
    }, []);

    const loadReports = async (page: number = currentPage) => {
        setLoading(true);
        try {
            const response = await api.getReports({ page, limit: itemsPerPage });
            setReports(response.data);
            if (response.pagination) {
                setTotalPages(response.pagination.totalPages);
                setTotalItems(response.pagination.totalItems);
                setCurrentPage(page);
            }
        } catch (error) {
            console.error('Failed to load reports:', error);
        } finally {
            setLoading(false);
        }
    };

    const handlePageChange = (page: number) => {
        loadReports(page);
        window.scrollTo({ top: 0, behavior: 'smooth' });
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

    const handlePreview = async (scanId: string) => {
        setPreviewLoading(true);
        try {
            const blob = await api.downloadReport(scanId, 'html');
            const html = await blob.text();
            setPreviewReport(html);
        } catch (error) {
            console.error('Failed to preview report:', error);
            alert('Failed to preview report');
        } finally {
            setPreviewLoading(false);
        }
    };

    if (loading) {
        return (
            <>
                <header className="section-header">
                    <h1 className="section-title">Reports</h1>
                    <p className="section-subtitle">View and download historical scan reports.</p>
                </header>
                <SkeletonTable rows={10} columns={5} />
            </>
        );
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
                                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                                <button
                                                    onClick={() => handlePreview(report.id)}
                                                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem', border: '1px solid var(--primary-start)', borderRadius: 'var(--radius-md)', background: 'white', color: 'var(--primary-start)', cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500 }}
                                                >
                                                    👁️ Preview
                                                </button>
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

                {/* Pagination */}
                {!loading && reports.length > 0 && (
                    <Pagination
                        currentPage={currentPage}
                        totalPages={totalPages}
                        totalItems={totalItems}
                        itemsPerPage={itemsPerPage}
                        onPageChange={handlePageChange}
                        loading={loading}
                    />
                )}
            </div>

            {/* Preview Modal */}
            {(previewReport || previewLoading) && (
                <div
                    style={{
                        position: 'fixed',
                        inset: 0,
                        background: 'rgba(0,0,0,0.7)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                        padding: '2rem'
                    }}
                    onClick={() => setPreviewReport(null)}
                >
                    <div
                        style={{
                            background: 'white',
                            borderRadius: 'var(--radius-md)',
                            width: '90%',
                            maxWidth: '1200px',
                            height: '90vh',
                            display: 'flex',
                            flexDirection: 'column',
                            overflow: 'hidden'
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ margin: 0, fontSize: '1.3rem' }}>Report Preview</h2>
                            <button
                                onClick={() => setPreviewReport(null)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    fontSize: '1.5rem',
                                    cursor: 'pointer',
                                    color: 'var(--text-secondary)',
                                    padding: '0.5rem'
                                }}
                            >
                                ×
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
                            {previewLoading ? (
                                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                    <p>Loading preview...</p>
                                </div>
                            ) : (
                                <iframe
                                    srcDoc={previewReport || ''}
                                    style={{
                                        width: '100%',
                                        height: '100%',
                                        border: '1px solid var(--border-light)',
                                        borderRadius: 'var(--radius-md)'
                                    }}
                                    title="Report Preview"
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
