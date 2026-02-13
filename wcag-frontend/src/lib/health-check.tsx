/**
 * Backend Health Check Hook
 *
 * Monitors backend connection status and displays indicator.
 */

'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v2', '') || 'http://localhost:8000';

export type HealthStatus = 'healthy' | 'unhealthy' | 'checking';

export interface HealthCheckResult {
  status: HealthStatus;
  version?: string;
  lastCheck?: Date;
  error?: string;
}

export function useHealthCheck(intervalMs: number = 30000) {
  const [health, setHealth] = useState<HealthCheckResult>({
    status: 'checking'
  });

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/health`, {
          timeout: 5000
        });

        setHealth({
          status: 'healthy',
          version: response.data.version,
          lastCheck: new Date()
        });
      } catch (error: any) {
        setHealth({
          status: 'unhealthy',
          lastCheck: new Date(),
          error: error.message || 'Backend unavailable'
        });
      }
    };

    // Check immediately
    checkHealth();

    // Check periodically
    const interval = setInterval(checkHealth, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs]);

  return health;
}

// Health Status Indicator Component
export function HealthIndicator() {
  const health = useHealthCheck(30000); // Check every 30 seconds
  const [showDetails, setShowDetails] = useState(false);

  const getStatusColor = () => {
    switch (health.status) {
      case 'healthy':
        return '#10b981';
      case 'unhealthy':
        return '#ef4444';
      case 'checking':
        return '#f59e0b';
    }
  };

  const getStatusText = () => {
    switch (health.status) {
      case 'healthy':
        return 'Backend Online';
      case 'unhealthy':
        return 'Backend Offline';
      case 'checking':
        return 'Checking...';
    }
  };

  if (health.status === 'healthy') {
    // Don't show indicator if healthy
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '1rem',
        right: '1rem',
        zIndex: 9998,
        background: 'white',
        padding: '0.75rem 1rem',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)',
        border: `2px solid ${getStatusColor()}`,
        cursor: 'pointer',
        minWidth: '200px'
      }}
      onClick={() => setShowDetails(!showDetails)}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {/* Status Dot */}
        <div
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: getStatusColor(),
            animation: health.status === 'checking' ? 'pulse 2s infinite' : 'none'
          }}
        />

        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-main)' }}>
            {getStatusText()}
          </div>
          {showDetails && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {health.lastCheck && `Last check: ${health.lastCheck.toLocaleTimeString()}`}
              {health.error && <div style={{ color: '#ef4444', marginTop: '0.25rem' }}>{health.error}</div>}
              {health.version && <div style={{ marginTop: '0.25rem' }}>Version: {health.version}</div>}
            </div>
          )}
        </div>

        {/* Info Icon */}
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0, color: 'var(--text-secondary)' }}>
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
}
