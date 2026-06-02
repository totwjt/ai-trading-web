import { createApiClient } from '@/api/client'

const authApiClient = createApiClient()

interface ApiResponse<T> {
  code: number
  message: string
  data: T
  timestamp: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface UserProfile {
  id: number
  uid?: string
  username: string
  phone?: string
  email?: string
  created_at?: string
  updated_at?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserProfile
}

export interface TokenRefreshRequest {
  refresh_token: string
}

export interface TokenRefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface TokenRevokeResponse {
  message: string
}

export interface CreateUserRequest {
  username: string
  password: string
  phone: string
  email?: string
}

export async function loginAPI(payload: LoginRequest): Promise<LoginResponse> {
  const response = await authApiClient.post<ApiResponse<LoginResponse>>('/api/auth/login', payload)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '登录失败')
  }
  return response.data.data
}

export async function checkTokenAPI(accessToken: string): Promise<boolean> {
  const response = await authApiClient.get<ApiResponse<{ valid: boolean }>>('/api/auth/token/check', {
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  })
  if (response.data.code !== 0) {
    throw new Error(response.data.message || 'Token校验失败')
  }
  return response.data.data?.valid === true
}

export async function refreshTokenAPI(payload: TokenRefreshRequest): Promise<TokenRefreshResponse> {
  const response = await authApiClient.post<ApiResponse<TokenRefreshResponse>>('/api/auth/token/refresh', payload)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || 'Token刷新失败')
  }
  return response.data.data
}

export async function revokeTokenAPI(accessToken: string): Promise<TokenRevokeResponse> {
  const response = await authApiClient.post<ApiResponse<TokenRevokeResponse>>(
    '/api/auth/token/revoke',
    {},
    {
      headers: {
        Authorization: `Bearer ${accessToken}`
      }
    }
  )
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '退出登录失败')
  }
  return response.data.data
}

export async function getUsersAPI(page = 1, pageSize = 20): Promise<UserProfile[]> {
  const response = await authApiClient.get<ApiResponse<UserProfile[]>>('/api/auth/users', {
    params: {
      page,
      page_size: pageSize
    }
  })
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '获取用户列表失败')
  }
  return Array.isArray(response.data.data) ? response.data.data : []
}

export async function createUserAPI(payload: CreateUserRequest): Promise<UserProfile> {
  const response = await authApiClient.post<ApiResponse<UserProfile>>('/api/auth/users', payload)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '创建用户失败')
  }
  return response.data.data
}

export async function deleteUserAPI(userId: number): Promise<boolean> {
  const response = await authApiClient.delete<ApiResponse<Record<string, unknown>>>(`/api/auth/users/${userId}`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '删除用户失败')
  }
  return true
}
