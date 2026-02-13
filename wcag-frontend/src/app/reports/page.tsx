import { MockAPI } from "@/lib/mock-data";

export default async function ReportsPage() {
    const scans = await MockAPI.getScans();

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
                                <th>Type</th>
                                <th>Score</th>
                                <th>Issues</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {scans.map((scan) => (
                                <tr key={scan.id}>
                                    <td>{new Date(scan.createdAt).toLocaleDateString()}</td>
                                    <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{scan.url}</td>
                                    <td>{scan.projectName ? 'Project' : 'Quick'}</td>
                                    <td>{scan.score ? `${scan.score}%` : '—'}</td>
                                    <td>{scan.issuesCount || 0}</td>
                                    <td>
                                        <span className={`status-pill ${scan.status === 'completed' ? 'status-success' : scan.status === 'failed' ? 'status-danger' : 'status-warning'}`}>
                                            {scan.status}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <button className="btn-gradient" style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem' }}>HTML</button>
                                            <button style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}>JSON</button>
                                            <button style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit' }}>CSV</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
