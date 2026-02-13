/**
 * TypeScript types matching wcag-backend API v2 responses
 */

// ========== Authentication ==========

export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginResponse {
  success: boolean;
  data: {
    user: User;
    accessToken: string;
    refreshToken: string;
    expiresIn: number;
  };
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// ========== Projects ==========

export interface Project {
  id: string;
  userId: string;
  name: string;
  url: string;
  description?: string;
  status: 'active' | 'archived';
  createdAt: string;
  updatedAt: string;
  lastScan?: string;
  score?: number;
}

export interface CreateProjectRequest {
  name: string;
  url: string;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  url?: string;
  description?: string;
  status?: 'active' | 'archived';
}

// ========== Scans ==========

export type ScanStatus = 'queued' | 'scanning' | 'completed' | 'failed';
export type ScanType = 'quick' | 'full';

export interface ScanProgress {
  pagesScanned: number;
  totalPages: number;
  currentUrl?: string;
  percentage: number;
}

export interface IssuesByImpact {
  critical: number;
  serious: number;
  moderate: number;
  minor: number;
}

export interface Scan {
  id: string;
  userId: string;
  projectId?: string;
  url: string;
  type: ScanType;
  status: ScanStatus;
  config: {
    maxPages?: number;
    maxDepth?: number;
    scanners?: string[];
  };
  progress?: ScanProgress;
  score?: number;
  issuesCount?: number;
  issuesByImpact?: IssuesByImpact;
  duration?: number;
  createdAt: string;
  completedAt?: string;
  projectName?: string; // Populated by frontend
}

export interface QuickScanRequest {
  url: string;
  scanners?: string[];
}

export interface ProjectScanRequest {
  projectId: string;
  maxPages?: number;
  maxDepth?: number;
  scanners?: string[];
}

export interface ScanStatusResponse {
  success: boolean;
  data: {
    scanId: string;
    status: ScanStatus;
    progress?: ScanProgress;
    score?: number;
    issuesCount?: number;
    completedAt?: string;
  };
}

// ========== Issues ==========

export type ImpactLevel = 'critical' | 'serious' | 'moderate' | 'minor';
export type WCAGLevel = 'A' | 'AA' | 'AAA';
export type IssueStatus = 'open' | 'fixed' | 'ignored';

export interface Issue {
  id: string;
  scanId: string;
  userId: string;
  pageUrl: string;
  description: string;
  impact: ImpactLevel;
  wcagCriteria: string;
  wcagLevel: WCAGLevel;
  selector: string;
  htmlSnippet?: string;
  howToFix?: string;
  helpUrl?: string;
  status: IssueStatus;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateIssueRequest {
  status: IssueStatus;
}

// ========== Dashboard ==========

export interface DashboardStats {
  totalScans: number;
  completedScans: number;
  activeProjects: number;
  criticalIssues: number;
  totalIssues: number;
  avgScore: number;
  issuesByImpact: IssuesByImpact;
}

export interface DashboardPage {
  scanId: string;
  url: string;
  projectName?: string;
  score: number;
  issuesCount: number;
  lastScanned: string;
  status: ScanStatus;
}

// ========== Reports ==========

export type ReportFormat = 'html' | 'json' | 'csv';

export interface Report {
  id: string;
  projectName?: string;
  url: string;
  score: number;
  issuesCount: number;
  completedAt: string;
}

// ========== API Responses ==========

export interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: {
    items: T[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

// ========== Pagination ==========

export interface PaginationParams {
  page?: number;
  limit?: number;
}

export interface ProjectListParams extends PaginationParams {
  status?: 'active' | 'archived';
}

export interface ScanListParams extends PaginationParams {
  projectId?: string;
  status?: ScanStatus;
}

export interface IssueListParams extends PaginationParams {
  impact?: ImpactLevel;
  status?: IssueStatus;
}
