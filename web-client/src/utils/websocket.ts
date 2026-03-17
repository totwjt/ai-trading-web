import { ref, onUnmounted } from 'vue'

function generateClientId(): string {
  const stored = localStorage.getItem('ws_client_id')
  if (stored) return stored
  
  const newId = 'client_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36)
  localStorage.setItem('ws_client_id', newId)
  return newId
}

const CLIENT_ID = generateClientId()

export type MessageType = 
  | 'recommendation' 
  | 'heartbeat' 
  | 'system' 
  | 'subscribe' 
  | 'unsubscribe' 
  | 'connect' 
  | 'disconnect'

export interface WSMessage {
  type: MessageType
  payload: Record<string, unknown>
  timestamp: string
  message_id: string
}

export interface News {
  title: string
  content: string
  publish_time: string
  crawl_time: string
  source: string
  url: string
}

export interface Analysis {
  利好版块: string[]
  利好股票: string[]
  分析因素: string[]
  详细分析: string
}

export interface RecommendationData {
  news: News
  analysis: Analysis
}

export type MessageHandler = (data: RecommendationData) => void
export type ConnectHandler = () => void
export type DisconnectHandler = () => void
export type ErrorHandler = (error: Event) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectInterval = 3000
  private heartbeatInterval: number | null = null
  private isManualClose = false
  
  public isConnected = ref(false)
  public messageHandler: MessageHandler | null = null
  public connectHandler: ConnectHandler | null = null
  public disconnectHandler: DisconnectHandler | null = null
  public errorHandler: ErrorHandler | null = null

  constructor(url: string = 'ws://localhost:8765') {
    this.url = url
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.isManualClose = false
    
    try {
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = () => {
        this.isConnected.value = true
        this.startHeartbeat()
        this.sendConnect()
        this.connectHandler?.()
        console.log('[WS] 已连接')
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (e) {
          console.error('[WS] 解析消息失败:', e)
        }
      }

      this.ws.onclose = (event) => {
        this.isConnected.value = false
        this.stopHeartbeat()
        this.disconnectHandler?.()
        console.log('[WS] 连接关闭, code:', event.code, 'reason:', event.reason)
        
        if (!this.isManualClose) {
          console.log('[WS] 准备重连...')
          setTimeout(() => {
            console.log('[WS] 正在重连...')
            this.connect()
          }, this.reconnectInterval)
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WS] 错误:', error)
        this.errorHandler?.(error)
      }
    } catch (e) {
      console.error('[WS] 连接失败:', e)
    }
  }

  disconnect(): void {
    this.isManualClose = true
    this.stopHeartbeat()
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected.value = false
  }

  private handleMessage(message: WSMessage): void {
    switch (message.type) {
      case 'recommendation':
        this.messageHandler?.(message.payload as unknown as RecommendationData)
        break
      case 'heartbeat':
        console.log('[WS] 心跳')
        break
      case 'system':
        console.log('[WS] 系统消息:', message.payload)
        break
      default:
        break
    }
  }

  private sendConnect(): void {
    this.send({
      type: 'connect',
      payload: {
        client_id: CLIENT_ID,
        client_type: 'web',
        user_agent: navigator.userAgent
      },
      timestamp: new Date().toISOString(),
      message_id: `msg_${Date.now()}`
    })
  }

  subscribe(topics: string[]): void {
    this.send({
      type: 'subscribe',
      payload: {
        topics,
        client_type: 'web'
      },
      timestamp: new Date().toISOString(),
      message_id: `msg_${Date.now()}`
    })
  }

  private send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      this.send({
        type: 'heartbeat',
        payload: { status: 'ping' },
        timestamp: new Date().toISOString(),
        message_id: `msg_${Date.now()}`
      })
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

let wsClient: WebSocketClient | null = null

export function useWebSocket() {
  if (!wsClient) {
    wsClient = new WebSocketClient('ws://localhost:8765')
  }

  onUnmounted(() => {
  })

  return {
    wsClient,
    isConnected: wsClient.isConnected,
    connect: () => wsClient?.connect(),
    disconnect: () => wsClient?.disconnect(),
    subscribe: (topics: string[]) => wsClient?.subscribe(topics),
    onMessage: (handler: MessageHandler) => {
      wsClient!.messageHandler = handler
    },
    onConnect: (handler: ConnectHandler) => {
      wsClient!.connectHandler = handler
    },
    onDisconnect: (handler: DisconnectHandler) => {
      wsClient!.disconnectHandler = handler
    },
    onError: (handler: ErrorHandler) => {
      wsClient!.errorHandler = handler
    }
  }
}

export function parseStockInfo(stockStr: string): { code: string; name: string; score: number } | null {
  const match = stockStr.match(/(\d{6})\(([^)]+?)(\d+)?\)/)
  if (!match) return null
  
  return {
    code: match[1] + (parseInt(match[1]) < 500000 ? '.SH' : '.SZ'),
    name: match[2],
    score: match[3] ? parseInt(match[3]) : 0
  }
}
