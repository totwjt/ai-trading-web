export interface ApiConfig {
  ws: {
    host: string
    port: number
    path: string
  }
  recommendation: {
    host: string
    port: number
    path: string
  }
}

const config: ApiConfig = {
  ws: {
    host: import.meta.env.VITE_WS_HOST || 'localhost',
    port: Number(import.meta.env.VITE_WS_PORT) || 8766,
    path: import.meta.env.VITE_WS_PATH || '/pubsub'
  },
  recommendation: {
    host: import.meta.env.VITE_RECOMMENDATION_HOST || 'localhost',
    port: Number(import.meta.env.VITE_RECOMMENDATION_PORT) || 8766,
    path: import.meta.env.VITE_RECOMMENDATION_PATH || '/pubsub'
  }
}

export function getWsUrl(clientType: string): string {
  if (clientType === 'recommendation') {
    const { host, port, path } = config.recommendation
    return `ws://${host}:${port}${path}`
  }
  const { host, port, path } = config.ws
  return `ws://${host}:${port}${path}`
}

export default config
