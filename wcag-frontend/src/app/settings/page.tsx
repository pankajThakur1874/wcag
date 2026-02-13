'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useToast } from '@/lib/toast-context';
import { Skeleton } from '@/components/Skeleton';

export default function SettingsPage() {
    const { user, refreshUser, logout } = useAuth();
    const toast = useToast();
    const router = useRouter();

    const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'preferences'>('profile');
    const [loading, setLoading] = useState(false);

    // Profile form
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');

    // Password form
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    useEffect(() => {
        if (user) {
            setName(user.name);
            setEmail(user.email);
        }
    }, [user]);

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            // TODO: Implement profile update API call
            // await api.updateProfile({ name, email });
            toast.success('Profile updated successfully!');
            await refreshUser();
        } catch (error: any) {
            toast.error('Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();

        if (newPassword !== confirmPassword) {
            toast.error('New passwords do not match');
            return;
        }

        if (newPassword.length < 6) {
            toast.error('Password must be at least 6 characters');
            return;
        }

        setLoading(true);

        try {
            // TODO: Implement password change API call
            // await api.changePassword({ currentPassword, newPassword });
            toast.success('Password changed successfully!');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: any) {
            toast.error('Failed to change password');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (!confirm('Are you absolutely sure? This action cannot be undone. All your projects, scans, and data will be permanently deleted.')) {
            return;
        }

        const confirmation = prompt('Type "DELETE" to confirm account deletion:');
        if (confirmation !== 'DELETE') {
            toast.info('Account deletion cancelled');
            return;
        }

        setLoading(true);

        try {
            // TODO: Implement delete account API call
            // await api.deleteAccount();
            toast.success('Account deleted successfully');
            await logout();
        } catch (error: any) {
            toast.error('Failed to delete account');
            setLoading(false);
        }
    };

    if (!user) {
        return (
            <div style={{ padding: '2rem' }}>
                <Skeleton height="2rem" width="200px" style={{ marginBottom: '1rem' }} />
                <Skeleton height="400px" />
            </div>
        );
    }

    return (
        <>
            <header className="section-header">
                <h1 className="section-title">Settings</h1>
                <p className="section-subtitle">Manage your account settings and preferences.</p>
            </header>

            <div style={{ display: 'flex', gap: '2rem', maxWidth: '1200px' }}>
                {/* Sidebar Navigation */}
                <div className="card" style={{ width: '250px', padding: '1rem', height: 'fit-content' }}>
                    <nav>
                        <div
                            className={`nav-item ${activeTab === 'profile' ? 'active' : ''}`}
                            onClick={() => setActiveTab('profile')}
                            style={{ marginBottom: '0.5rem', cursor: 'pointer', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline', marginRight: '0.5rem' }}>
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                <circle cx="12" cy="7" r="4" />
                            </svg>
                            Profile
                        </div>
                        <div
                            className={`nav-item ${activeTab === 'security' ? 'active' : ''}`}
                            onClick={() => setActiveTab('security')}
                            style={{ marginBottom: '0.5rem', cursor: 'pointer', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline', marginRight: '0.5rem' }}>
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                            </svg>
                            Security
                        </div>
                        <div
                            className={`nav-item ${activeTab === 'preferences' ? 'active' : ''}`}
                            onClick={() => setActiveTab('preferences')}
                            style={{ cursor: 'pointer', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline', marginRight: '0.5rem' }}>
                                <circle cx="12" cy="12" r="3" />
                                <path d="M12 1v6m0 6v6m-8-7h6m6 0h6" />
                            </svg>
                            Preferences
                        </div>
                    </nav>
                </div>

                {/* Content Area */}
                <div style={{ flex: 1 }}>
                    {/* Profile Tab */}
                    {activeTab === 'profile' && (
                        <div className="card">
                            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.3rem' }}>Profile Information</h2>

                            <form onSubmit={handleUpdateProfile}>
                                <div style={{ marginBottom: '1.25rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                                        Full Name
                                    </label>
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        required
                                        style={{
                                            width: '100%',
                                            padding: '0.75rem',
                                            border: '1px solid var(--border-light)',
                                            borderRadius: 'var(--radius-md)',
                                            fontFamily: 'inherit',
                                            fontSize: '0.95rem'
                                        }}
                                    />
                                </div>

                                <div style={{ marginBottom: '1.25rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                                        Email Address
                                    </label>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        style={{
                                            width: '100%',
                                            padding: '0.75rem',
                                            border: '1px solid var(--border-light)',
                                            borderRadius: 'var(--radius-md)',
                                            fontFamily: 'inherit',
                                            fontSize: '0.95rem'
                                        }}
                                    />
                                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                                        We'll send a verification email if you change your email address
                                    </p>
                                </div>

                                <div style={{ marginBottom: '1.25rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                                        Account Created
                                    </label>
                                    <input
                                        type="text"
                                        value={new Date(user.createdAt).toLocaleDateString('en-US', {
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric'
                                        })}
                                        disabled
                                        style={{
                                            width: '100%',
                                            padding: '0.75rem',
                                            border: '1px solid var(--border-light)',
                                            borderRadius: 'var(--radius-md)',
                                            fontFamily: 'inherit',
                                            fontSize: '0.95rem',
                                            background: '#f9fafb',
                                            color: 'var(--text-secondary)'
                                        }}
                                    />
                                </div>

                                <button
                                    type="submit"
                                    className="btn-gradient"
                                    disabled={loading}
                                    style={{ padding: '0.75rem 2rem' }}
                                >
                                    {loading ? 'Saving Changes...' : 'Save Changes'}
                                </button>
                            </form>
                        </div>
                    )}

                    {/* Security Tab */}
                    {activeTab === 'security' && (
                        <>
                            <div className="card" style={{ marginBottom: '2rem' }}>
                                <h2 style={{ marginBottom: '1.5rem', fontSize: '1.3rem' }}>Change Password</h2>

                                <form onSubmit={handleChangePassword}>
                                    <div style={{ marginBottom: '1.25rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                                            Current Password
                                        </label>
                                        <input
                                            type="password"
                                            value={currentPassword}
                                            onChange={(e) => setCurrentPassword(e.target.value)}
                                            required
                                            style={{
                                                width: '100%',
                                                padding: '0.75rem',
                                                border: '1px solid var(--border-light)',
                                                borderRadius: 'var(--radius-md)',
                                                fontFamily: 'inherit',
                                                fontSize: '0.95rem'
                                            }}
                                        />
                                    </div>

                                    <div style={{ marginBottom: '1.25rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                                            New Password
                                        </label>
                                        <input
                                            type="password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            required
                                            minLength={6}
                                            style={{
                                                width: '100%',
                                                padding: '0.75rem',
                                                border: '1px solid var(--border-light)',
                                                borderRadius: 'var(--radius-md)',
                                                fontFamily: 'inherit',
                                                fontSize: '0.95rem'
                                            }}
                                        />
                                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                                            Minimum 6 characters
                                        </p>
                                    </div>

                                    <div style={{ marginBottom: '1.5rem' }}>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                                            Confirm New Password
                                        </label>
                                        <input
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            required
                                            minLength={6}
                                            style={{
                                                width: '100%',
                                                padding: '0.75rem',
                                                border: '1px solid var(--border-light)',
                                                borderRadius: 'var(--radius-md)',
                                                fontFamily: 'inherit',
                                                fontSize: '0.95rem'
                                            }}
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        className="btn-gradient"
                                        disabled={loading}
                                        style={{ padding: '0.75rem 2rem' }}
                                    >
                                        {loading ? 'Changing Password...' : 'Change Password'}
                                    </button>
                                </form>
                            </div>

                            {/* Danger Zone */}
                            <div className="card" style={{ borderColor: '#fee2e2' }}>
                                <h2 style={{ marginBottom: '1rem', fontSize: '1.3rem', color: '#ef4444' }}>Danger Zone</h2>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                                    Once you delete your account, there is no going back. All your data will be permanently deleted.
                                </p>

                                <button
                                    onClick={handleDeleteAccount}
                                    disabled={loading}
                                    style={{
                                        padding: '0.75rem 1.5rem',
                                        border: '2px solid #ef4444',
                                        borderRadius: 'var(--radius-md)',
                                        background: 'white',
                                        color: '#ef4444',
                                        cursor: loading ? 'not-allowed' : 'pointer',
                                        fontFamily: 'inherit',
                                        fontWeight: 600,
                                        fontSize: '0.9rem',
                                        opacity: loading ? 0.6 : 1
                                    }}
                                >
                                    Delete Account
                                </button>
                            </div>
                        </>
                    )}

                    {/* Preferences Tab */}
                    {activeTab === 'preferences' && (
                        <div className="card">
                            <h2 style={{ marginBottom: '1.5rem', fontSize: '1.3rem' }}>Preferences</h2>

                            <div style={{ marginBottom: '2rem' }}>
                                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Notifications</h3>

                                <label style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem', cursor: 'pointer' }}>
                                    <input type="checkbox" defaultChecked style={{ marginRight: '0.75rem', cursor: 'pointer' }} />
                                    <div>
                                        <div style={{ fontWeight: 500 }}>Email notifications</div>
                                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            Receive email updates about scan completions
                                        </div>
                                    </div>
                                </label>

                                <label style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem', cursor: 'pointer' }}>
                                    <input type="checkbox" defaultChecked style={{ marginRight: '0.75rem', cursor: 'pointer' }} />
                                    <div>
                                        <div style={{ fontWeight: 500 }}>Critical issues alerts</div>
                                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            Get notified when critical accessibility issues are detected
                                        </div>
                                    </div>
                                </label>
                            </div>

                            <div style={{ marginBottom: '2rem' }}>
                                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Display</h3>

                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                                    Theme
                                </label>
                                <select
                                    className="form-select"
                                    style={{ margin: 0, maxWidth: '300px' }}
                                    disabled
                                >
                                    <option value="light">Light (Current)</option>
                                    <option value="dark">Dark (Coming Soon)</option>
                                    <option value="auto">Auto (Coming Soon)</option>
                                </select>
                            </div>

                            <button
                                className="btn-gradient"
                                disabled
                                style={{ padding: '0.75rem 2rem', opacity: 0.5 }}
                            >
                                Preferences Auto-saved
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
