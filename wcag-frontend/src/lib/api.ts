/**
 * WCAG Backend API v2 Client
 *
 * Axios-based HTTP client for communicating with the FastAPI backend.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  ApiResponse,
  PaginatedResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectListParams,
  Scan,
  QuickScanRequest,
  ProjectScanRequest,
  ScanStatusResponse,
  ScanListParams,
  Issue,
  IssueListParams,
  UpdateIssueRequest,
  DashboardStats,
  DashboardPage,
  Report,
  ReportFormat,
} from './types';

// ========== Configuration ==========

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v2';

// ========== Token Management ==========

export const TokenStorage = {
  getAccessToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },

  getRefreshToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  },

  setTokens: (accessToken: string, refreshToken: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  },

  clearTokens: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  getUser: (): User | null => {
    if (typeof window === 'undefined') return null;
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  setUser: (user: User): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('user', JSON.stringify(user));
  },
};

// ========== Axios Instance ==========

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add access token
    this.client.interceptors.request.use(
      (config) => {
        const token = TokenStorage.getAccessToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // If token expired, try to refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Wait for token refresh to complete
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`;
                }
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const refreshToken = TokenStorage.getRefreshToken();
            if (!refreshToken) {
              throw new Error('No refresh token');
            }

            const response = await axios.post<LoginResponse>(
              `${API_BASE_URL}/auth/refresh`,
              { refreshToken }
            );

            const { accessToken, refreshToken: newRefreshToken } = response.data.data;
            TokenStorage.setTokens(accessToken, newRefreshToken);

            // Retry all queued requests
            this.refreshSubscribers.forEach((callback) => callback(accessToken));
            this.refreshSubscribers = [];

            // Retry original request
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${accessToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout
            TokenStorage.clearTokens();
            if (typeof window !== 'undefined') {
              window.location.href = '/login';
            }
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // ========== Authentication ==========

  async register(data: RegisterRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/register', data);
    const { user, accessToken, refreshToken } = response.data.data;
    TokenStorage.setTokens(accessToken, refreshToken);
    TokenStorage.setUser(user);
    return response.data;
  }

  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', data);
    const { user, accessToken, refreshToken } = response.data.data;
    TokenStorage.setTokens(accessToken, refreshToken);
    TokenStorage.setUser(user);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = TokenStorage.getRefreshToken();
      if (refreshToken) {
        await this.client.post('/auth/logout', { refreshToken });
      }
    } finally {
      TokenStorage.clearTokens();
    }
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await this.client.get<ApiResponse<User>>('/auth/me');
    TokenStorage.setUser(response.data.data);
    return response.data;
  }

  async refreshToken(): Promise<LoginResponse> {
    const refreshToken = TokenStorage.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await this.client.post<LoginResponse>('/auth/refresh', { refreshToken });
    const { accessToken, refreshToken: newRefreshToken } = response.data.data;
    TokenStorage.setTokens(accessToken, newRefreshToken);
    return response.data;
  }

  // ========== Projects ==========

  async getProjects(params?: ProjectListParams): Promise<PaginatedResponse<Project>> {
    const response = await this.client.get<PaginatedResponse<Project>>('/projects', { params });
    return response.data;
  }

  async createProject(data: CreateProjectRequest): Promise<ApiResponse<Project>> {
    const response = await this.client.post<ApiResponse<Project>>('/projects', data);
    return response.data;
  }

  async getProject(id: string): Promise<ApiResponse<Project>> {
    const response = await this.client.get<ApiResponse<Project>>(`/projects/${id}`);
    return response.data;
  }

  async updateProject(id: string, data: UpdateProjectRequest): Promise<ApiResponse<Project>> {
    const response = await this.client.put<ApiResponse<Project>>(`/projects/${id}`, data);
    return response.data;
  }

  async deleteProject(id: string): Promise<ApiResponse<{ message: string }>> {
    const response = await this.client.delete<ApiResponse<{ message: string }>>(`/projects/${id}`);
    return response.data;
  }

  // ========== Scans ==========

  async startQuickScan(data: QuickScanRequest): Promise<ApiResponse<{ scanId: string; status: string }>> {
    const response = await this.client.post<ApiResponse<{ scanId: string; status: string }>>('/scans/quick', data);
    return response.data;
  }

  async startProjectScan(data: ProjectScanRequest): Promise<ApiResponse<{ scanId: string; status: string }>> {
    const response = await this.client.post<ApiResponse<{ scanId: string; status: string }>>('/scans/project', data);
    return response.data;
  }

  async getScanStatus(scanId: string): Promise<ScanStatusResponse> {
    const response = await this.client.get<ScanStatusResponse>(`/scans/${scanId}/status`);
    return response.data;
  }

  async getScans(params?: ScanListParams): Promise<PaginatedResponse<Scan>> {
    const response = await this.client.get<PaginatedResponse<Scan>>('/scans', { params });
    return response.data;
  }

  async getScan(id: string): Promise<ApiResponse<Scan>> {
    const response = await this.client.get<ApiResponse<Scan>>(`/scans/${id}`);
    return response.data;
  }

  // ========== Issues ==========

  async getIssues(scanId: string, params?: IssueListParams): Promise<PaginatedResponse<Issue>> {
    const response = await this.client.get<PaginatedResponse<Issue>>(`/scans/${scanId}/issues`, { params });
    return response.data;
  }

  async updateIssue(issueId: string, data: UpdateIssueRequest): Promise<ApiResponse<Issue>> {
    const response = await this.client.patch<ApiResponse<Issue>>(`/issues/${issueId}`, data);
    return response.data;
  }

  // ========== Dashboard ==========

  async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    const response = await this.client.get<ApiResponse<DashboardStats>>('/dashboard/stats');
    return response.data;
  }

  async getDashboardPages(params?: { page?: number; limit?: number }): Promise<PaginatedResponse<DashboardPage>> {
    const response = await this.client.get<PaginatedResponse<DashboardPage>>('/dashboard/pages', { params });
    return response.data;
  }

  // ========== Reports ==========

  async getReports(params?: { page?: number; limit?: number }): Promise<PaginatedResponse<Report>> {
    const response = await this.client.get<PaginatedResponse<Report>>('/reports', { params });
    return response.data;
  }

  async downloadReport(scanId: string, format: ReportFormat): Promise<Blob> {
    const response = await this.client.get(`/reports/${scanId}/download`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  // ========== Helper: Download Report as File ==========

  downloadReportAsFile(blob: Blob, filename: string): void {
    if (typeof window === 'undefined') return;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

// ========== Export Singleton Instance ==========

export const api = new ApiClient();
export default api;
