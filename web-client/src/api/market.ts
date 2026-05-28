import axios from 'axios'

function getApiBaseUrl(): string {
  if ((import.meta as any).env?.VITE_API_URL) {
    return (import.meta as any).env.VITE_API_URL
  }
  return `http://${window.location.hostname}:8766`
}

const API_BASE_URL = getApiBaseUrl()

const marketApiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface HsgtTop10Item {
  trade_date: string
  ts_code: string
  name: string
  close: number
  change: number
  rank: number
  market_type: string
  amount: number | null
  net_amount: number | null
  buy: number | null
  sell: number | null
}

export interface HsgtTop10Response {
  trade_date: string
  market_type: string
  count: number
  data: HsgtTop10Item[]
}

export interface IndexSpotItem {
  code: string
  name: string
  latest_price: number
  change_pct: number
  change_amount: number
  prev_close: number
  open_price: number
  high: number
  low: number
  volume: number
  amount: number
}

export interface IndexSpotResponse {
  update_time: string
  count: number
  data: IndexSpotItem[]
}

export interface HotSearchItem {
  trade_date: string
  symbol: string
  code?: string | null
  ts_code?: string | null
  name_code: string
  change_pct: string
  hot_score: number
}

export interface HotSearchResponse {
  trade_date: string
  symbol: string
  count: number
  data: HotSearchItem[]
}

export interface ZtPoolItem {
  seq: number
  ts_code: string
  name: string
  change_pct: number
  close_price: number
  amount: number
  float_mv: number
  total_mv: number
  turnover_rate: number
  seal_amount: number
  first_seal_time: string | null
  last_seal_time: string | null
  break_seal_count: number
  zt_statistics: string | null
  continuous_count: number
  industry: string | null
}

export interface DtPoolItem {
  seq: number
  ts_code: string
  name: string
  change_pct: number
  close_price: number
  amount: number
  float_mv: number
  total_mv: number
  pe: number | null
  turnover_rate: number
  seal_amount: number
  last_seal_time: string | null
  board_amount: number
  continuous_days: number
  open_board_count: number
  industry: string | null
}

export interface PoolResponse<T> {
  update_time: string
  count: number
  data: T[]
}

export function getHsgtTop10(marketType?: string): Promise<HsgtTop10Response> {
  return marketApiClient
    .get<HsgtTop10Response>('/api/market/hsgt/top10', {
      params: marketType ? { market_type: marketType } : undefined
    })
    .then(response => response.data)
}

export function getHotSearchList(symbol?: string): Promise<HotSearchResponse> {
  return marketApiClient
    .get<HotSearchResponse>('/api/market/hot_search/list', {
      params: symbol ? { symbol } : undefined
    })
    .then(response => response.data)
}

export function getIndexSpot(): Promise<IndexSpotResponse> {
  return marketApiClient.get<IndexSpotResponse>('/api/market/index/spot').then(response => response.data)
}

export function getZtPool(): Promise<PoolResponse<ZtPoolItem>> {
  return marketApiClient.get<PoolResponse<ZtPoolItem>>('/api/market/zt/pool').then(response => response.data)
}

export function getDtPool(): Promise<PoolResponse<DtPoolItem>> {
  return marketApiClient.get<PoolResponse<DtPoolItem>>('/api/market/dt/pool').then(response => response.data)
}
