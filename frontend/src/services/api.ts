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
    options: RequestInit = {}
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

    let response: Response;
    try {
      response = await fetch(url, { ...options, headers });
    } catch (networkErr: any) {
      // True network failure (backend not running, DNS failure, etc.)
      throw new Error(
        `Cannot connect to the Marine Intelligence Platform backend at ${API_BASE_URL}. ` +
        `Please ensure the backend server is running. (${networkErr.message})`
      );
    }

    if (!response.ok) {
      if (response.status === 401) {
        // Clear invalid/expired token so the user gets redirected to login on next render.
        ApiClient.setToken(null);
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

      let detailMsg: string | null = null;
      const rawDetail = (errorBody as any)?.detail;
      if (Array.isArray(rawDetail)) {
        detailMsg = rawDetail
          .map((err: any) => {
            const field = Array.isArray(err.loc) ? err.loc.slice(1).join('.') : err.loc || '';
            return field ? `${field}: ${err.msg}` : err.msg;
          })
          .join('; ');
      }

      const message =
        (errorBody as any)?.error?.message ||
        (errorBody as any)?.detail?.message ||
        detailMsg ||
        (typeof rawDetail === 'string' ? rawDetail : null) ||
        `Request failed with status ${response.status}`;

      throw new Error(message);
    }

    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return { data: null as unknown as T, meta: { timestamp: new Date().toISOString() } };
    }

    let json: any;
    try {
      json = await response.json();
    } catch {
      return { data: null as unknown as T, meta: { timestamp: new Date().toISOString() } };
    }

    // Backend wraps responses as { data, meta } — unwrap if present
    if (json && typeof json === 'object' && 'data' in json) {
      return json;
    }
    return { data: json, meta: { timestamp: new Date().toISOString() } };
  }

  static get<T>(endpoint: string, queryParamsOrFallback?: unknown, explicitQueryParams?: Record<string, any>) {
    let queryParams: Record<string, any> | undefined = undefined;
    if (explicitQueryParams && typeof explicitQueryParams === 'object' && !Array.isArray(explicitQueryParams)) {
      queryParams = explicitQueryParams;
    } else if (queryParamsOrFallback && typeof queryParamsOrFallback === 'object' && !Array.isArray(queryParamsOrFallback)) {
      // Only treat as queryParams if it doesn't look like a rich domain model (e.g. not having complex nested objects)
      const obj = queryParamsOrFallback as Record<string, any>;
      const hasComplexObjects = Object.values(obj).some(v => v !== null && typeof v === 'object');
      if (!hasComplexObjects) {
        queryParams = obj;
      }
    }

    let url = endpoint;
    if (queryParams) {
      const params = new URLSearchParams();
      Object.entries(queryParams).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
            params.append(key, String(val));
          }
        }
      });
      const qs = params.toString();
      if (qs) {
        url += (url.includes('?') ? '&' : '?') + qs;
      }
    }
    return this.request<T>(url, { method: 'GET' });
  }

  static post<T>(endpoint: string, body?: any, _unused?: unknown) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: isFormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      }
    );
  }

  static patch<T>(endpoint: string, body?: any, _unused?: unknown) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: isFormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      }
    );
  }

  static put<T>(endpoint: string, body?: any, _unused?: unknown) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: isFormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
      }
    );
  }

  static delete<T>(endpoint: string, _unused?: unknown) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}
