import { MockAPI } from "@/lib/mock-data";

export default async function ProjectsPage() {
    const projects = await MockAPI.getProjects();

    return (
        <>
            <header className="section-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                    <h1 className="section-title">Projects</h1>
                    <p className="section-subtitle">Manage your websites and scan configurations.</p>
                </div>
                <button className="btn-gradient">+ New Project</button>
            </header>

            <div className="projects-grid">
                {projects.map((project) => (
                    <div key={project.id} className="card project-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h3 style={{ fontWeight: 600 }}>{project.name}</h3>
                            <span className={`status-pill ${project.status === 'active' ? 'status-success' : 'status-warning'}`}>
                                {project.status}
                            </span>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>{project.url}</p>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            <span>Last scan: {new Date(project.lastScan).toLocaleDateString()}</span>
                            <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>Score: {project.score}%</span>
                        </div>
                        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
                            <button className="btn-gradient" style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}>Scan Now</button>
                            <button style={{ padding: '0.5rem 1rem', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'inherit', fontSize: '0.8rem' }}>Settings</button>
                        </div>
                    </div>
                ))}
            </div>
        </>
    );
}
