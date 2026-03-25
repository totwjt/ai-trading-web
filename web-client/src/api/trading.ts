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
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ==================== 类型定义 ====================

export interface StockSearchResult {
  ts_code: string
  name: string
  industry: string | null
  market: string | null
  list_date: string | null
}

export interface StockSearchResponse {
  code: number
  message: string
  data: StockSearchResult[]
  total: number
  timestamp: string
}

// 实时行情
export interface StockRealtime {
  ts_code: string
  trade_time: string | null
  open: number
  high: number
  low: number
  close: number
  vol: number
}

// 自选股票（包含实时行情）
export interface WatchlistItem {
  ts_code: string
  name: string
  pre_close?: number
  open?: number
  high?: number
  low?: number
  close?: number
  change?: number
  change_pct?: number
  vol?: number
  amount?: number
  num?: number
  ask_price1?: number
  ask_volume1?: number
  bid_price1?: number
  bid_volume1?: number
  trade_time?: string
}

// 策略配置
export interface StrategyConfig {
  enabled: boolean
  riseSpeedMin: number  // 最小涨速百分比
  riseSpeedMax: number  // 最大涨速百分比
  volumeMin: number     // 最小成交量
  priceMin: number      // 最低价格
  priceMax: number      // 最高价格
}

// 交易记录
export interface TradeRecord {
  id: number
  ts_code: string
  name: string
  direction: 'buy' | 'sell'
  price: number
  quantity: number
  amount: number
  time: string
  status: 'success' | 'failed'
}

// ==================== API 函数 ====================

/**
 * 股票检索 - 支持按股票代码或名称模糊查询
 */
export async function searchStocks(keyword: string, limit: number = 20): Promise<StockSearchResult[]> {
  const response = await apiClient.get<StockSearchResponse>('/api/trading/stock/search', {
    params: { keyword, limit }
  })
  
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  
  return response.data.data || []
}

/**
 * 获取股票实时行情
 */
export async function getStockRealtime(tsCode: string): Promise<StockRealtime> {
  const response = await apiClient.get<StockRealtime>(`/api/trading/stock/realtime/${tsCode}`)
  return response.data
}

/**
 * 获取自选股票列表
 */
export async function getWatchlist(): Promise<WatchlistItem[]> {
  const response = await apiClient.get<{ code: number; data: WatchlistItem[] }>('/api/trading/watchlist')
  return response.data.data || []
}

export async function addToWatchlistAPI(tsCode: string, _name: string): Promise<boolean> {
  const response = await apiClient.post<{ code: number; message?: string }>(`/api/trading/watchlist/${tsCode}`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '添加失败')
  }
  return true
}

export async function removeFromWatchlistAPI(tsCode: string): Promise<boolean> {
  const response = await apiClient.delete<{ code: number; message?: string }>(`/api/trading/watchlist/${tsCode}`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '删除失败')
  }
  return true
}

/**
 * 获取策略配置
 */
export async function getStrategyConfig(): Promise<StrategyConfig> {
  // TODO: 后端实现后接入
  return {
    enabled: false,
    riseSpeedMin: 0,
    riseSpeedMax: 5,
    volumeMin: 1000,
    priceMin: 1,
    priceMax: 100
  }
}

/**
 * 保存策略配置
 */
export async function saveStrategyConfig(config: StrategyConfig): Promise<boolean> {
  // TODO: 后端实现后接入
  console.log('保存策略配置:', config)
  return true
}

/**
 * 获取交易记录
 */
export async function getTradeRecords(): Promise<TradeRecord[]> {
  try {
    const response = await apiClient.get<{ code: number; data: TradeRecord[] }>('/api/trading/trades')
    if (response.data.code === 0) {
      return response.data.data || []
    }
    return []
  } catch (error) {
    console.error('获取交易记录失败:', error)
    return []
  }
}