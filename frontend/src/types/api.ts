export interface ApiResponseMeta {
  page?: number;
  pageSize?: number;
  total?: number;
  timestamp?: string;
  source?: string;
}

export interface ApiResponse<T> {
  data: T;
  meta?: ApiResponseMeta;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}
