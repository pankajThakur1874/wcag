'use client';

import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { usePathname } from 'next/navigation';
import { AuthProvider, useAuth } from '@/lib/auth-context';

function LayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login';

  // Don't require auth for login page
  if (isAuthPage) {
    return <>{children}</>;
  }

  // Show authenticated layout with sidebar
  const { user } = useAuth();
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
        <AuthProvider>
          <LayoutContent>{children}</LayoutContent>
        </AuthProvider>
      </body>
    </html>
  );
}
