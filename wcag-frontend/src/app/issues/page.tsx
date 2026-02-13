import { MockAPI } from "@/lib/mock-data";

export default async function IssuesPage() {
    const issues = await MockAPI.getIssues();

    const impactColor: Record<string, string> = {
        critical: 'impact-critical',
        serious: 'impact-serious',
        moderate: 'impact-moderate',
        minor: 'impact-minor',
    };

    return (
        <>
            <header className="section-header">
                <h1 className="section-title">Issues</h1>
                <p className="section-subtitle">Review detected accessibility violations.</p>
            </header>

            {/* Report Selector */}
            <div className="report-controls">
                <label style={{ fontWeight: 600 }}>Select Report:</label>
                <select className="form-select" style={{ margin: 0, maxWidth: '400px' }}>
                    <option value="">-- Choose a Scan Report --</option>
                    <option value="1">Corporate Website — Jan 15, 2025</option>
                    <option value="2">E-commerce App — Jan 12, 2025</option>
                </select>
                <button className="btn-gradient" style={{ background: 'var(--text-secondary)' }}>Refresh</button>
            </div>

            {/* Issues List */}
            <div>
                {issues.map((issue) => (
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
                ))}
            </div>
        </>
    );
}
