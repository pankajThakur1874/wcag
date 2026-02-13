'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { SkeletonStats, SkeletonCard, SkeletonTable } from '@/components/Skeleton';
import type { DashboardStats, DashboardPage } from '@/lib/types';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pages, setPages] = useState<DashboardPage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsRes, pagesRes] = await Promise.all([
          api.getDashboardStats(),
          api.getDashboardPages({ limit: 10 })
        ]);
        setStats(statsRes.data);
        setPages(pagesRes.data);
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading || !stats) {
    return (
      <>
        <header className="section-header">
          <h1 className="section-title">Dashboard</h1>
          <p className="section-subtitle">Overview of your accessibility compliance status.</p>
        </header>

        <SkeletonStats />

        <div className="charts-row">
          <SkeletonCard />
          <SkeletonCard />
        </div>

        <SkeletonTable rows={5} columns={6} />
      </>
    );
  }

  const score = Math.round(stats.avgScore || 0);
  const dashOffset = 440 - (440 * score) / 100;

  // Calculate bar widths based on total issues
  const impact = stats.issuesByImpact || { critical: 0, serious: 0, moderate: 0, minor: 0 };
  const totalIssues = stats.totalIssues || (impact.critical + impact.serious + impact.moderate + impact.minor) || 1;
  const getBarPercentage = (count: number) => Math.max(Math.round((count / totalIssues) * 100), count > 0 ? 5 : 0);

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
          <div className="stat-value">{stats.completedScans}</div>
          <div className="stat-label">Completed Scans</div>
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
          <div className="stat-value">{Math.round(stats.avgScore)}%</div>
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
              { label: 'Critical', value: getBarPercentage(impact.critical), count: impact.critical, color: 'var(--grad-danger)' },
              { label: 'Serious', value: getBarPercentage(impact.serious), count: impact.serious, color: 'linear-gradient(135deg, var(--accent-orange), #ea580c)' },
              { label: 'Moderate', value: getBarPercentage(impact.moderate), count: impact.moderate, color: 'var(--grad-warning)' },
              { label: 'Minor', value: getBarPercentage(impact.minor), count: impact.minor, color: 'var(--grad-success)' },
            ].map((bar) => (
              <div key={bar.label} className="bar-row">
                <span className="bar-label">{bar.label} ({bar.count})</span>
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
        <h3 style={{ marginBottom: '1rem' }}>Recently Scanned Pages</h3>
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
              {pages.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    No scans yet. Start your first scan from the Scan page.
                  </td>
                </tr>
              ) : (
                pages.map((page) => (
                  <tr key={page.scanId}>
                    <td>{page.url}</td>
                    <td>{page.projectName || 'Quick Scan'}</td>
                    <td>{page.score}%</td>
                    <td>{page.issuesCount}</td>
                    <td>{new Date(page.lastScanned).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-pill ${page.status === 'completed' ? 'status-success' : page.status === 'failed' ? 'status-danger' : 'status-warning'}`}>
                        {page.status}
                      </span>
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
