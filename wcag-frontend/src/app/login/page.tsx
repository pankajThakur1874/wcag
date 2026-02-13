'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const router = useRouter();
    const [isRegister, setIsRegister] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        // Simulate auth delay
        await new Promise(r => setTimeout(r, 1000));
        setLoading(false);
        router.push('/');
    };

    const bypassAuth = () => {
        router.push('/');
    };

    return (
        <div className="auth-overlay">
            <div className="auth-box">
                {/* Left Panel — Gradient Branding */}
                <div className="auth-left">
                    <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>WCAG Scanner</h1>
                    <p style={{ fontSize: '1.25rem', opacity: 0.9 }}>Comprehensive Accessibility Testing Platform</p>
                    <div style={{ marginTop: 'auto' }}>
                        <p>✓ WCAG 2.2 Compliance</p>
                        <p>✓ Automated &amp; Manual Checks</p>
                        <p>✓ Detailed Reports</p>
                    </div>
                </div>

                {/* Right Panel — Forms */}
                <div className="auth-right">
                    <h2 style={{ marginBottom: '1.5rem' }}>
                        {isRegister ? 'Create Account' : 'Welcome Back'}
                    </h2>

                    {!isRegister ? (
                        /* Login Form */
                        <form onSubmit={handleSubmit}>
                            <input
                                type="email"
                                className="auth-input"
                                placeholder="Email Address"
                                required
                                defaultValue="demo@example.com"
                            />
                            <input
                                type="password"
                                className="auth-input"
                                placeholder="Password"
                                required
                                defaultValue="password123"
                            />
                            <button
                                type="submit"
                                className="btn-gradient w-full flex-center"
                                style={{ padding: '1rem', width: '100%', justifyContent: 'center' }}
                                disabled={loading}
                            >
                                {loading ? 'Signing In...' : 'Sign In'}
                            </button>
                            <p style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.9rem' }}>
                                Don&apos;t have an account?{' '}
                                <a
                                    href="#"
                                    style={{ color: 'var(--primary-start)', fontWeight: 500 }}
                                    onClick={(e) => { e.preventDefault(); setIsRegister(true); }}
                                >
                                    Register
                                </a>
                            </p>
                            {error && (
                                <p style={{ color: 'red', textAlign: 'center', fontSize: '0.8rem', marginTop: '0.5rem' }}>{error}</p>
                            )}
                            <p style={{ textAlign: 'center', marginTop: '1rem' }}>
                                <a
                                    href="#"
                                    style={{ color: '#94a3b8', fontSize: '0.8rem' }}
                                    onClick={(e) => { e.preventDefault(); bypassAuth(); }}
                                >
                                    [Dev: Skip Auth]
                                </a>
                            </p>
                        </form>
                    ) : (
                        /* Register Form */
                        <form onSubmit={handleSubmit}>
                            <input
                                type="text"
                                className="auth-input"
                                placeholder="Full Name"
                                required
                            />
                            <input
                                type="email"
                                className="auth-input"
                                placeholder="Email Address"
                                required
                            />
                            <input
                                type="password"
                                className="auth-input"
                                placeholder="Password"
                                required
                            />
                            <button
                                type="submit"
                                className="btn-gradient w-full flex-center"
                                style={{ padding: '1rem', width: '100%', justifyContent: 'center' }}
                                disabled={loading}
                            >
                                {loading ? 'Creating Account...' : 'Create Account'}
                            </button>
                            <p style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.9rem' }}>
                                Already have an account?{' '}
                                <a
                                    href="#"
                                    style={{ color: 'var(--primary-start)', fontWeight: 500 }}
                                    onClick={(e) => { e.preventDefault(); setIsRegister(false); }}
                                >
                                    Sign In
                                </a>
                            </p>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
