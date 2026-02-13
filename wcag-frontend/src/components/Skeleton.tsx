/**
 * Skeleton Loading Components
 *
 * Reusable skeleton loaders for better loading states.
 */

import React, { CSSProperties } from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  style?: CSSProperties;
}

export function Skeleton({ width = '100%', height = '1rem', borderRadius = '0.25rem', style }: SkeletonProps) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        background: 'linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
        ...style
      }}
    >
      <style jsx>{`
        @keyframes shimmer {
          0% {
            background-position: 200% 0;
          }
          100% {
            background-position: -200% 0;
          }
        }
      `}</style>
    </div>
  );
}

export function SkeletonText({ lines = 3, style }: { lines?: number; style?: CSSProperties }) {
  return (
    <div style={style}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height="0.875rem"
          width={i === lines - 1 ? '70%' : '100%'}
          style={{ marginBottom: '0.5rem' }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <Skeleton height="1.5rem" width="60%" style={{ marginBottom: '1rem' }} />
      <SkeletonText lines={3} />
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
        <Skeleton height="2.5rem" width="100px" />
        <Skeleton height="2.5rem" width="100px" />
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="card">
      <div className="table-container">
        <table>
          <thead>
            <tr>
              {Array.from({ length: columns }).map((_, i) => (
                <th key={i}>
                  <Skeleton height="1rem" width="80%" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, rowIndex) => (
              <tr key={rowIndex}>
                {Array.from({ length: columns }).map((_, colIndex) => (
                  <td key={colIndex}>
                    <Skeleton height="0.875rem" width={colIndex === 0 ? '100%' : '60%'} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function SkeletonStats() {
  return (
    <div className="stats-grid">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card stat-card">
          <div className="stat-top-bar" style={{ background: 'var(--primary-gradient)' }} />
          <Skeleton height="2.5rem" width="60%" style={{ marginBottom: '0.5rem' }} />
          <Skeleton height="1rem" width="80%" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonProjectCard() {
  return (
    <div className="card project-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <Skeleton height="1.5rem" width="40%" />
        <Skeleton height="1.5rem" width="60px" borderRadius="1rem" />
      </div>
      <Skeleton height="0.875rem" width="90%" style={{ marginBottom: '0.5rem' }} />
      <Skeleton height="0.875rem" width="70%" style={{ marginBottom: '1rem' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', marginTop: '1rem' }}>
        <Skeleton height="0.875rem" width="40%" />
        <Skeleton height="0.875rem" width="30%" />
      </div>
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
        <Skeleton height="2rem" width="100px" />
        <Skeleton height="2rem" width="100px" />
      </div>
    </div>
  );
}

export function SkeletonIssueCard() {
  return (
    <div className="card issue-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem', gap: '1rem' }}>
        <Skeleton height="1.25rem" width="60%" />
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Skeleton height="1.5rem" width="80px" borderRadius="1rem" />
          <Skeleton height="1.5rem" width="60px" borderRadius="1rem" />
        </div>
      </div>
      <Skeleton height="0.875rem" width="90%" style={{ marginBottom: '0.5rem' }} />
      <Skeleton height="0.875rem" width="100%" style={{ marginBottom: '0.75rem' }} />
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
        <Skeleton height="2rem" width="120px" />
        <Skeleton height="2rem" width="140px" />
      </div>
    </div>
  );
}
