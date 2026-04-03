import axios from 'axios'

function getApiBaseUrl(): string {
  if ((import.meta as any).env?.VITE_API_URL) {
    return (import.meta as any).env.VITE_API_URL
  }
  return `http://${window.location.hostname}:8766`
}

const API_BASE_URL = getApiBaseUrl()

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
  timestamp: string
}

export interface PaginationMeta {
  total: number
  page: number
  page_size: number
}

export interface StrategyConfig {
  initial_capital: number
  commission: number
  slippage: number
  use_min_commission: boolean
  min_commission: number
  fill_ratio: number
  adjust_mode: string
  benchmark_code: string
  symbols: string[]
  match_mode: string
}

export interface Strategy {
  id: number
  name: string
  strategy_type: string | null
  status: 'running' | 'paused' | 'stopped' | 'error'
  code?: string
  config?: StrategyConfig
  description?: string
  created_at: string
  updated_at: string
}

export interface StrategyListItem {
  id: number
  name: string
  strategy_type: string | null
  status: 'running' | 'paused' | 'stopped' | 'error'
  created_at: string
  updated_at: string
}

export interface StrategyListResponse {
  total: number
  page: number
  page_size: number
  items: StrategyListItem[]
}

export interface StrategyCreate {
  name: string
  strategy_type?: string
  code: string
  config?: StrategyConfig
  description?: string
}

export interface StrategyUpdate {
  name?: string
  strategy_type?: string
  code?: string
  config?: StrategyConfig
  description?: string
}

export async function getStrategyList(params?: {
  page?: number
  page_size?: number
  status?: string
}): Promise<{ items: StrategyListItem[]; total: number; page: number; page_size: number }> {
  const response = await apiClient.get<ApiResponse<StrategyListResponse>>('/api/strategies', { params })
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function getStrategyDetail(id: number): Promise<Strategy> {
  const response = await apiClient.get<ApiResponse<Strategy>>(`/api/strategies/${id}`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function createStrategy(data: StrategyCreate): Promise<{ id: number; name: string }> {
  const response = await apiClient.post<ApiResponse<{ id: number; name: string }>>('/api/strategies', data)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function updateStrategy(id: number, data: StrategyUpdate): Promise<{ id: number; updated_at: string }> {
  const response = await apiClient.put<ApiResponse<{ id: number; updated_at: string }>>(`/api/strategies/${id}`, data)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function deleteStrategy(id: number): Promise<void> {
  const response = await apiClient.delete<ApiResponse<null>>(`/api/strategies/${id}`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
}

export async function strategyAction(id: number, action: 'start' | 'stop' | 'pause'): Promise<{ id: number; status: string }> {
  const response = await apiClient.post<ApiResponse<{ id: number; status: string }>>(`/api/strategies/${id}/action`, { action })
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}
