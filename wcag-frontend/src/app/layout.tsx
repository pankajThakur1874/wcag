'use client';

import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { usePathname, useRouter } from 'next/navigation';
import { AuthProvider, useAuth } from '@/lib/auth-context';
import { ToastProvider } from '@/lib/toast-context';
import { HealthIndicator } from '@/lib/health-check';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useEffect } from 'react';

function LayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = pathname === '/login';
  const { user, loading } = useAuth();

  // Don't require auth for login page
  if (isAuthPage) {
    return <>{children}</>;
  }

  // Show loading state while checking auth
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{ color: 'white', fontSize: '1.2rem' }}>Loading...</div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user && !isAuthPage) {
      router.push('/login');
    }
  }, [user, loading, isAuthPage, router]);

  // Don't render protected content if not authenticated
  if (!user) {
    return null;
  }

  // Show authenticated layout with sidebar
  const initials = user?.name
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase() || 'U';

  return (
    <>
      <Sidebar />
      <main className="main-content">
        {/* Top Bar */}
        <header className="top-bar">
          <div className="search-bar">
            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21L16.65 16.65" />
            </svg>
            <input type="text" placeholder="Search pages, issues..." />
          </div>
          <div className="user-menu">
            <button className="btn-gradient" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem' }}>Docs</button>
            <button
              onClick={() => window.location.href = '/settings'}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.8rem',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)',
                background: 'white',
                cursor: 'pointer',
                fontFamily: 'inherit'
              }}
            >
              Settings
            </button>
            <div className="user-avatar" title={user?.name || 'User'}>{initials}</div>
          </div>
        </header>
        {children}
      </main>
    </>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login';

  return (
    <html lang="en">
      <head>
        <title>{isAuthPage ? 'WCAG Scanner - Login' : 'WCAG Scanner - Premium Dashboard'}</title>
        <meta name="description" content={isAuthPage ? 'Sign in to WCAG Scanner' : 'Comprehensive Accessibility Testing Platform'} />
      </head>
      <body>
        <ErrorBoundary>
          <ToastProvider>
            <AuthProvider>
              <LayoutContent>{children}</LayoutContent>
              <HealthIndicator />
            </AuthProvider>
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
