// --- Types ---

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface Project {
  id: string;
  name: string;
  url: string;
  description?: string;
  lastScan: string;
  status: 'active' | 'archived';
  score: number;
}

export interface Scan {
  id: string;
  projectId?: string;
  projectName?: string;
  url: string;
  type: 'quick' | 'full';
  status: 'queued' | 'scanning' | 'completed' | 'failed';
  score?: number;
  issuesCount?: number;
  createdAt: string;
  duration?: number;
}

export interface Issue {
  id: string;
  scanId: string;
  description: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  wcagCriteria: string;
  selector: string;
  htmlSnippet?: string;
  helpUrl?: string;
  howToFix?: string;
  status: 'open' | 'ignored' | 'fixed';
}

// --- Mock Data ---

const MOCK_USER: User = {
  id: 'u1',
  name: 'Demo User',
  email: 'demo@example.com'
};

const MOCK_PROJECTS: Project[] = [
  { id: 'p1', name: 'Corporate Website', url: 'https://example.com', status: 'active', score: 92, lastScan: '2025-01-15T10:00:00Z' },
  { id: 'p2', name: 'E-commerce App', url: 'https://shop.example.com', status: 'active', score: 68, lastScan: '2025-01-12T14:30:00Z' },
  { id: 'p3', name: 'Gov Portal', url: 'https://portal.gov.example', status: 'active', score: 85, lastScan: '2025-01-10T09:00:00Z' },
  { id: 'p4', name: 'Legacy Blog', url: 'https://old-blog.com', status: 'archived', score: 45, lastScan: '2024-12-01T09:15:00Z' },
];

const MOCK_SCANS: Scan[] = [
  { id: 's1', projectId: 'p1', projectName: 'Corporate Website', url: 'https://example.com', type: 'full', status: 'completed', score: 92, issuesCount: 3, createdAt: '2025-01-15T10:00:00Z', duration: 45 },
  { id: 's2', projectId: 'p2', projectName: 'E-commerce App', url: 'https://shop.example.com/products', type: 'full', status: 'completed', score: 68, issuesCount: 12, createdAt: '2025-01-12T14:30:00Z', duration: 120 },
  { id: 's3', projectId: 'p1', projectName: 'Corporate Website', url: 'https://example.com/about', type: 'quick', status: 'completed', score: 88, issuesCount: 5, createdAt: '2025-01-11T11:00:00Z', duration: 30 },
  { id: 's4', projectId: 'p3', projectName: 'Gov Portal', url: 'https://portal.gov.example', type: 'full', status: 'completed', score: 85, issuesCount: 7, createdAt: '2025-01-10T09:00:00Z', duration: 60 },
  { id: 's5', url: 'https://google.com', type: 'quick', status: 'completed', score: 95, issuesCount: 1, createdAt: '2025-01-09T16:00:00Z', duration: 15 },
];

const MOCK_ISSUES: Issue[] = [
  { id: 'i1', scanId: 's2', description: 'Images must have alternate text', impact: 'critical', wcagCriteria: '1.1.1', selector: 'img.hero-banner', htmlSnippet: '<img src="banner.jpg" />', howToFix: 'Add an alt attribute with descriptive text to the image.', status: 'open' },
  { id: 'i2', scanId: 's2', description: 'Form elements must have labels', impact: 'serious', wcagCriteria: '1.3.1, 3.3.2', selector: 'input#email', htmlSnippet: '<input type="email" name="email" />', howToFix: 'Associate a <label> element with each form input using for/id attributes.', status: 'open' },
  { id: 'i3', scanId: 's2', description: 'Links must have discernible text', impact: 'moderate', wcagCriteria: '2.4.4, 4.1.2', selector: 'a.read-more', htmlSnippet: '<a href="/post/1"></a>', howToFix: 'Provide visible or screen-reader text inside the link.', status: 'fixed' },
  { id: 'i4', scanId: 's1', description: 'Contrast ratio is not sufficient', impact: 'serious', wcagCriteria: '1.4.3', selector: 'button.submit', htmlSnippet: '<button style="color:#aaa">Submit</button>', howToFix: 'Ensure text color has a contrast ratio of at least 4.5:1 against its background.', status: 'open' },
  { id: 'i5', scanId: 's4', description: 'Page must have one main landmark', impact: 'moderate', wcagCriteria: '1.3.1', selector: 'body', howToFix: 'Add a <main> element to identify the primary content region.', status: 'open' },
  { id: 'i6', scanId: 's3', description: 'Color should not be used as the only visual means of conveying information', impact: 'minor', wcagCriteria: '1.4.1', selector: '.status-indicator', howToFix: 'Use text, shapes, or patterns in addition to color to convey information.', status: 'open' },
];

// --- Mock API Helpers ---

export const MockAPI = {
  login: async (email: string): Promise<User> => {
    await new Promise(r => setTimeout(r, 800));
    if (email === 'fail@test.com') throw new Error('Invalid credentials');
    return MOCK_USER;
  },

  getProjects: async (): Promise<Project[]> => {
    await new Promise(r => setTimeout(r, 100));
    return [...MOCK_PROJECTS];
  },

  getScans: async (): Promise<Scan[]> => {
    await new Promise(r => setTimeout(r, 100));
    return [...MOCK_SCANS];
  },

  getIssues: async (filter?: string): Promise<Issue[]> => {
    await new Promise(r => setTimeout(r, 100));
    return filter ? MOCK_ISSUES.filter(i => i.impact === filter) : [...MOCK_ISSUES];
  },

  getStats: async () => {
    return {
      totalScans: MOCK_SCANS.length,
      activeProjects: MOCK_PROJECTS.filter(p => p.status === 'active').length,
      criticalIssues: MOCK_ISSUES.filter(i => i.impact === 'critical').length,
      avgScore: 78
    };
  }
};
