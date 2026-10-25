export type LocalAPIErrorCode =
  | 'NETWORK_ERROR'
  | 'FILE_NOT_FOUND'
  | 'PERMISSION_DENIED'
  | 'VALIDATION_ERROR'
  | 'SERVER_ERROR'
  | 'UNKNOWN_ERROR'

export interface LocalAPIError {
  code: LocalAPIErrorCode
  message: string
  details?: string
  originalError?: unknown
}

export interface RetryConfig {
  maxRetries: number
  retryDelay: number
  backoffFactor: number
}

export const ErrorCode = {
  NETWORK_ERROR: 'NETWORK_ERROR' as const,
  FILE_NOT_FOUND: 'FILE_NOT_FOUND' as const,
  PERMISSION_DENIED: 'PERMISSION_DENIED' as const,
  VALIDATION_ERROR: 'VALIDATION_ERROR' as const,
  SERVER_ERROR: 'SERVER_ERROR' as const,
  UNKNOWN_ERROR: 'UNKNOWN_ERROR' as const,
}
