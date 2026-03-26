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
  speed_1min?: number
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
  buy_5m: number   // 买点涨幅
  sell_5m: number  // 卖点跌幅
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
  try {
    const response = await apiClient.get<{ switchSta: boolean; buy_5m: number; sell_5m: number }>('/strategy_info')
    return {
      enabled: response.data.switchSta ?? false,
      buy_5m: response.data.buy_5m ?? 0,
      sell_5m: response.data.sell_5m ?? 0
    }
  } catch (error) {
    console.error('获取策略配置失败:', error)
    return {
      enabled: false,
      buy_5m: 0,
      sell_5m: 0
    }
  }
}

/**
 * 设置策略开关
 */
export async function setStrategySwitch(enabled: boolean): Promise<boolean> {
  try {
    await apiClient.post('/strategy_action', { action: 'switch', sta: enabled })
    return true
  } catch (error) {
    console.error('设置策略开关失败:', error)
    return false
  }
}

/**
 * 设置买点涨幅
 */
export async function setBuyThreshold(value: number): Promise<boolean> {
  try {
    await apiClient.post('/strategy_action', { action: 'buy', type: '5m', value })
    return true
  } catch (error) {
    console.error('设置买点涨幅失败:', error)
    return false
  }
}

/**
 * 设置卖点跌幅
 */
export async function setSellThreshold(value: number): Promise<boolean> {
  try {
    await apiClient.post('/strategy_action', { action: 'sell', type: '5m', value })
    return true
  } catch (error) {
    console.error('设置卖点跌幅失败:', error)
    return false
  }
}

/**
 * 保存策略配置（兼容旧接口，内部调用各自分接口）
 */
export async function saveStrategyConfig(config: StrategyConfig): Promise<boolean> {
  try {
    await setStrategySwitch(config.enabled)
    await setBuyThreshold(config.buy_5m)
    await setSellThreshold(config.sell_5m)
    return true
  } catch (error) {
    console.error('保存策略配置失败:', error)
    return false
  }
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

/**
 * 获取系统连接状态
 */
export async function getSystemStatus(): Promise<boolean> {
  try {
    const response = await apiClient.get<{ code: number; data: boolean }>('/api/trading/system_status')
    if (response.data.code === 0) {
      return response.data.data === true
    }
    return false
  } catch (error) {
    console.error('获取系统状态失败:', error)
    return false
  }
}