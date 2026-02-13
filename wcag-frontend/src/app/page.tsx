import { MockAPI } from "@/lib/mock-data";

export default async function Dashboard() {
  const stats = await MockAPI.getStats();
  const scans = await MockAPI.getScans();

  const score = stats.avgScore;
  const dashOffset = 440 - (440 * score) / 100;

  return (
    <>
      <header className="section-header">
        <h1 className="section-title">Dashboard</h1>
        <p className="section-subtitle">Overview of your accessibility compliance status.</p>
      </header>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="card stat-card">
          <div className="stat-top-bar" style={{ background: 'var(--primary-gradient)' }} />
          <div className="stat-value">{stats.totalScans}</div>
          <div className="stat-label">Total Scans</div>
        </div>
        <div className="card stat-card">
          <div className="stat-top-bar" style={{ background: 'var(--grad-info)' }} />
          <div className="stat-value">{stats.activeProjects}</div>
          <div className="stat-label">Active Projects</div>
        </div>
        <div className="card stat-card">
          <div className="stat-top-bar" style={{ background: 'var(--grad-danger)' }} />
          <div className="stat-value">{stats.criticalIssues}</div>
          <div className="stat-label">Critical Issues</div>
        </div>
        <div className="card stat-card">
          <div className="stat-top-bar" style={{ background: 'var(--grad-success)' }} />
          <div className="stat-value">{score}%</div>
          <div className="stat-label">Average Score</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Compliance Gauge */}
        <div className="card flex-center" style={{ flexDirection: 'column' }}>
          <h3 style={{ marginBottom: '1rem' }}>Compliance Score</h3>
          <div className="gauge-container">
            <svg className="gauge-svg" viewBox="0 0 200 200">
              <defs>
                <linearGradient id="gauge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style={{ stopColor: 'var(--primary-start)' }} />
                  <stop offset="100%" style={{ stopColor: 'var(--primary-end)' }} />
                </linearGradient>
              </defs>
              <circle className="gauge-bg" cx="100" cy="100" r="70" />
              <circle className="gauge-fill" cx="100" cy="100" r="70" style={{ strokeDashoffset: dashOffset }} />
            </svg>
            <div className="gauge-text">
              <div className="gauge-score">{score}%</div>
              <small style={{ color: 'var(--text-secondary)' }}>Overall</small>
            </div>
          </div>
        </div>

        {/* Issues by Impact Bar Chart */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Issues by Impact</h3>
          <div className="bar-chart">
            {[
              { label: 'Critical', value: 35, color: 'var(--grad-danger)' },
              { label: 'Serious', value: 55, color: 'linear-gradient(135deg, var(--accent-orange), #ea580c)' },
              { label: 'Moderate', value: 70, color: 'var(--grad-warning)' },
              { label: 'Minor', value: 25, color: 'var(--grad-success)' },
            ].map((bar) => (
              <div key={bar.label} className="bar-row">
                <span className="bar-label">{bar.label}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${bar.value}%`, background: bar.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* All Scanned Pages Table */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>All Scanned Pages</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>URL</th>
                <th>Project</th>
                <th>Score</th>
                <th>Issues</th>
                <th>Last Scanned</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((scan) => (
                <tr key={scan.id}>
                  <td>{scan.url}</td>
                  <td>{scan.projectName || 'Quick Scan'}</td>
                  <td>{scan.score ? `${scan.score}%` : '—'}</td>
                  <td>{scan.issuesCount || 0}</td>
                  <td>{new Date(scan.createdAt).toLocaleDateString()}</td>
                  <td>
                    <span className={`status-pill ${scan.status === 'completed' ? 'status-success' : scan.status === 'failed' ? 'status-danger' : 'status-warning'}`}>
                      {scan.status}
                    </span>
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
