'use client';

import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { usePathname } from 'next/navigation';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login';

  if (isAuthPage) {
    return (
      <html lang="en">
        <head>
          <title>WCAG Scanner - Login</title>
          <meta name="description" content="Sign in to WCAG Scanner" />
        </head>
        <body>{children}</body>
      </html>
    );
  }

  return (
    <html lang="en">
      <head>
        <title>WCAG Scanner - Premium Dashboard</title>
        <meta name="description" content="Comprehensive Accessibility Testing Platform" />
      </head>
      <body>
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
              <div className="user-avatar">DU</div>
            </div>
          </header>
          {children}
        </main>
      </body>
    </html>
  );
}
