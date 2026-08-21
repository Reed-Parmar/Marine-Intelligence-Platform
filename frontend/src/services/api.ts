import { ApiResponse, ApiError } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export class ApiClient {
  private static token: string | null = localStorage.getItem('cmlre_auth_token');

  static setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('cmlre_auth_token', token);
    } else {
      localStorage.removeItem('cmlre_auth_token');
    }
  }

  static getToken(): string | null {
    return this.token || localStorage.getItem('cmlre_auth_token');
  }

  static async request<T>(
    endpoint: string,
    options: RequestInit = {},
    fallbackData?: T
  ): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
    
    const headers = new Headers(options.headers || {});

    if (!headers.has('Accept')) {
      headers.set('Accept', 'application/json');
    }

    if (!isFormData && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const token = this.getToken();
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        // If 401 Unauthorized, notify or clear session if needed
        if (response.status === 401) {
          console.warn('API returned 401 Unauthorized');
        }
        
        let errorBody: ApiError;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = {
            error: {
              code: `HTTP_${response.status}`,
              message: response.statusText || 'An error occurred during request execution',
            }
          };
        }

        // If fallback data exists (e.g. backend offline during hackathon demo), use fallback
        if (fallbackData !== undefined) {
          console.info(`Using CMLRE fallback fixture for ${endpoint} due to HTTP ${response.status}`);
          return { data: fallbackData, meta: { source: 'local_cmlre_engine', timestamp: new Date().toISOString() } };
        }

        throw new Error(errorBody.error.message || `Request failed with status ${response.status}`);
      }

      const json = await response.json();
      // If backend returns unwrapped data, wrap it in { data, meta }
      if (json && typeof json === 'object' && 'data' in json) {
        return json;
      }
      return { data: json, meta: { timestamp: new Date().toISOString() } };
    } catch (err: any) {
      // Network error (e.g. backend server not currently running locally) -> graceful fallback to mock data
      if (fallbackData !== undefined) {
        console.info(`Using offline CMLRE scientific engine fallback for ${endpoint}`);
        return { data: fallbackData, meta: { source: 'offline_cmlre_engine', timestamp: new Date().toISOString() } };
      }
      throw err;
    }
  }

  static get<T>(endpoint: string, fallbackData?: T, queryParams?: Record<string, any>) {
    let url = endpoint;
    if (queryParams) {
      const params = new URLSearchParams();
      Object.entries(queryParams).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          params.append(key, String(val));
        }
      });
      const qs = params.toString();
      if (qs) {
        url += (url.includes('?') ? '&' : '?') + qs;
      }
    }
    return this.request<T>(url, { method: 'GET' }, fallbackData);
  }

  static post<T>(endpoint: string, body?: any, fallbackData?: T) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: isFormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      },
      fallbackData
    );
  }

  static patch<T>(endpoint: string, body?: any, fallbackData?: T) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: isFormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      },
      fallbackData
    );
  }

  static put<T>(endpoint: string, body?: any, fallbackData?: T) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: isFormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      },
      fallbackData
    );
  }

  static delete<T>(endpoint: string, fallbackData?: T) {
    return this.request<T>(endpoint, { method: 'DELETE' }, fallbackData);
  }
}
