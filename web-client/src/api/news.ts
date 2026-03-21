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

export interface StockItem {
  name: string
  code: string | null
  score: number | null
}

export interface NewsItem {
  id: number
  title: string
  source: string
  publish_time: string | null
  analysis: string
  sectors: string[]
  stocks: StockItem[]
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  timestamp: string
}

export async function getLatestNews(limit: number = 10): Promise<NewsItem[]> {
  const response = await apiClient.get<ApiResponse<NewsItem[]>>('/api/news/latest', {
    params: { limit }
  })
  
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  
  return response.data.data || []
}

export async function getNewsDetail(newsId: number): Promise<NewsItem | null> {
  const response = await apiClient.get<ApiResponse<NewsItem[]>>(`/api/news/${newsId}`)
  
  if (response.data.code !== 0) {
    throw new Error(response.data.message)
  }
  
  return response.data.data?.[0] || null
}
