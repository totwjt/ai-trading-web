import axios from 'axios'
import type { ApiResponse } from './strategy'

function getApiBaseUrl(): string {
  if ((import.meta as any).env?.VITE_API_URL) {
    return (import.meta as any).env.VITE_API_URL
  }
  return `http://${window.location.hostname}:8766`
}

const API_BASE_URL = getApiBaseUrl()

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface BacktestParams {
  start_date: string
  end_date: string
  frequency: string
  initial_capital: number
}

export interface Backtest {
  id: number
  strategy_id: number
  strategy_name?: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  start_date: string
  end_date: string
  initial_capital: number
  frequency: string
  final_equity?: number
  total_return?: number
  benchmark_return?: number
  annual_return?: number
  max_drawdown?: number
  sharpe_ratio?: number
  win_rate?: number
  profit_loss_ratio?: number
  progress: number
  error_message?: string
  execution_time?: number
  created_at: string
  completed_at?: string
}

export interface BacktestListItem {
  id: number
  strategy_id: number
  strategy_name?: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  start_date: string
  end_date: string
  total_return?: number
  sharpe_ratio?: number
  progress: number
  created_at: string
}

export interface BacktestListResponse {
  total: number
  page: number
  page_size: number
  items: BacktestListItem[]
}

export interface BacktestDetail {
  backtest_id: number
  strategy_id: number
  strategy_name?: string
  status: string
  params: BacktestParams
  results: {
    final_equity?: number
    total_return?: number
    benchmark_return?: number
    annual_return?: number
    max_drawdown?: number
    sharpe_ratio?: number
    win_rate?: number
    profit_loss_ratio?: number
  }
  progress: number
  error_message?: string
  execution_time?: number
  created_at: string
  completed_at?: string
}

export interface TradeItem {
  id: number
  time: string
  code: string
  name?: string
  type: 'BUY' | 'SELL'
  price: number
  quantity: number
  amount: number
  profit?: number
  commission: number
}

export interface TradeListResponse {
  total: number
  page: number
  page_size: number
  items: TradeItem[]
}

export interface LogItem {
  time: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS'
  message: string
}

export interface LogListResponse {
  backtest_id: number
  error_count: number
  warning_count: number
  logs: LogItem[]
}

export interface EquityPoint {
  date: string
  equity: number
  benchmark: number
  returns: number
}

export interface EquityCurveResponse {
  backtest_id: number
  benchmark: string
  frequency: string
  data_points: EquityPoint[]
}

export interface PerformanceSummary {
  total_return?: number
  annual_return?: number
  max_drawdown?: number
  sharpe_ratio?: number
  win_rate?: number
  profit_loss_ratio?: number
}

export interface PerformanceMetrics {
  calmar_ratio?: number
  sortino_ratio?: number
  volatility?: number
  beta?: number
  alpha?: number
  information_ratio?: number
  max_consecutive_wins?: number
  max_consecutive_losses?: number
  avg_holding_days?: number
  total_trades?: number
  avg_profit_per_trade?: number
}

export interface PerformanceResponse {
  backtest_id: number
  summary: PerformanceSummary
  metrics: PerformanceMetrics
}

export interface PreviewResult {
  success: boolean
  logs: LogItem[]
  summary?: PerformanceSummary & { final_equity?: number; initial_value?: number }
  equity_curve?: EquityPoint[]
  error?: string
}

export async function getBacktestList(params?: {
  page?: number
  page_size?: number
  strategy_id?: number
  status?: string
}): Promise<{ items: BacktestListItem[]; total: number; page: number; page_size: number }> {
  const response = await apiClient.get<ApiResponse<BacktestListResponse>>('/api/backtests', { params })
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function createBacktest(strategyId: number, params: BacktestParams): Promise<{
  backtest_id: number
  strategy_id: number
  status: string
  progress: number
  created_at: string
}> {
  const response = await apiClient.post<ApiResponse<any>>('/api/backtests', {
    strategy_id: strategyId,
    params
  })
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function getBacktestDetail(id: number): Promise<BacktestDetail> {
  const response = await apiClient.get<ApiResponse<BacktestDetail>>(`/api/backtests/${id}`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function getBacktestProgress(id: number): Promise<{
  backtest_id: number
  status: string
  progress: number
  current_date?: string
  message?: string
}> {
  const response = await apiClient.get<ApiResponse<any>>(`/api/backtests/${id}/progress`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function cancelBacktest(id: number): Promise<{ backtest_id: number; status: string }> {
  const response = await apiClient.post<ApiResponse<any>>(`/api/backtests/${id}/cancel`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function getBacktestTrades(id: number, params?: {
  page?: number
  page_size?: number
}): Promise<{ items: TradeItem[]; total: number; page: number; page_size: number }> {
  const response = await apiClient.get<ApiResponse<TradeListResponse>>(`/api/backtests/${id}/trades`, { params })
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function getBacktestLogs(id: number): Promise<LogListResponse> {
  const response = await apiClient.get<ApiResponse<LogListResponse>>(`/api/backtests/${id}/logs`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function getEquityCurve(id: number, frequency: string = '1d'): Promise<EquityCurveResponse> {
  const response = await apiClient.get<ApiResponse<EquityCurveResponse>>(`/api/backtests/${id}/equity-curve`, {
    params: { frequency }
  })
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function getPerformance(id: number): Promise<PerformanceResponse> {
  const response = await apiClient.get<ApiResponse<PerformanceResponse>>(`/api/backtests/${id}/performance`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function previewStrategy(data: {
  strategy_id?: number
  code: string
  params: BacktestParams
}): Promise<PreviewResult> {
  const response = await apiClient.post<ApiResponse<PreviewResult>>('/api/backtests/preview', data)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}

export async function runBacktest(id: number): Promise<{ backtest_id: number; status: string }> {
  const response = await apiClient.post<ApiResponse<any>>(`/api/backtests/${id}/run`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  return response.data.data!
}
