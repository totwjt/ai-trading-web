/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WS_HOST: string
  readonly VITE_WS_PORT: string
  readonly VITE_WS_PATH: string
  readonly VITE_RECOMMENDATION_HOST: string
  readonly VITE_RECOMMENDATION_PORT: string
  readonly VITE_RECOMMENDATION_PATH: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
