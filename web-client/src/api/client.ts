import axios, { AxiosHeaders } from 'axios'
import type { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'

const ACCESS_TOKEN_KEY = 'ai_trading_access_token'

export function getApiBaseUrl(): string {
  if ((import.meta as any).env?.VITE_API_URL) {
    return (import.meta as any).env.VITE_API_URL
  }
  return `http://${window.location.hostname}:8766`
}

function getAccessToken(): string {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem(ACCESS_TOKEN_KEY)?.trim() || ''
}

function attachAuthorizationHeader(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  const token = getAccessToken()
  if (!token) return config

  const headers = AxiosHeaders.from(config.headers)
  if (!headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  config.headers = headers
  return config
}

export function createApiClient(config: AxiosRequestConfig = {}): AxiosInstance {
  const client = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json'
    },
    ...config
  })

  client.interceptors.request.use(attachAuthorizationHeader)

  return client
}
