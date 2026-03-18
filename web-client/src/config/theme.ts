export type ThemeMode = 'light' | 'dark'
export type ThemeScheme = 'default' | 'ocean' | 'forest'

export interface ThemeColors {
  primary: string
  up: string
  down: string
  warning: string
  border: string
  bgMain: string
  bgCard: string
  bgFloat: string
  textMain: string
  textSub: string
  textMute: string
}

export interface ThemeConfig {
  name: string
  colors: {
    light: ThemeColors
    dark: ThemeColors
  }
}

export const themes: Record<ThemeScheme, ThemeConfig> = {
  default: {
    name: '默认',
    colors: {
      light: {
        primary: '#2F6BFF',
        up: '#FF4D4F',
        down: '#00C087',
        warning: '#FAAD14',
        border: '#E5E7EB',
        bgMain: '#F5F7FA',
        bgCard: '#FFFFFF',
        bgFloat: '#FFFFFF',
        textMain: '#1F2937',
        textSub: '#6B7280',
        textMute: '#9CA3AF',
      },
      dark: {
        primary: '#2F6BFF',
        up: '#FF4D4F',
        down: '#00C087',
        warning: '#FAAD14',
        border: '#2D3A4D',
        bgMain: '#0B1A2A',
        bgCard: '#10243A',
        bgFloat: '#16324D',
        textMain: '#D6E4FF',
        textSub: '#8AA4C2',
        textMute: '#5A7A9A',
      },
    },
  },
  ocean: {
    name: '海洋',
    colors: {
      light: {
        primary: '#2FA4A9',
        up: '#FF4D4F',
        down: '#00C087',
        warning: '#FAAD14',
        border: '#CBD5E1',
        bgMain: '#F0F9FF',
        bgCard: '#FFFFFF',
        bgFloat: '#FFFFFF',
        textMain: '#0F172A',
        textSub: '#475569',
        textMute: '#94A3B8',
      },
      dark: {
        primary: '#2FA4A9',
        up: '#FF4D4F',
        down: '#00C087',
        warning: '#FAAD14',
        border: '#2D3A4D',
        bgMain: '#0B1A2A',
        bgCard: '#10243A',
        bgFloat: '#16324D',
        textMain: '#D6E4FF',
        textSub: '#8AA4C2',
        textMute: '#5A7A9A',
      },
    },
  },
  forest: {
    name: '森林',
    colors: {
      light: {
        primary: '#2BA471',
        up: '#FF4D4F',
        down: '#00C087',
        warning: '#FAAD14',
        border: '#D1D5DB',
        bgMain: '#F6F8F6',
        bgCard: '#FFFFFF',
        bgFloat: '#FFFFFF',
        textMain: '#1C1917',
        textSub: '#57534E',
        textMute: '#A8A29E',
      },
      dark: {
        primary: '#2BA471',
        up: '#FF4D4F',
        down: '#00C087',
        warning: '#FAAD14',
        border: '#2D3A4D',
        bgMain: '#0B1A2A',
        bgCard: '#10243A',
        bgFloat: '#16324D',
        textMain: '#D6E4FF',
        textSub: '#8AA4C2',
        textMute: '#5A7A9A',
      },
    },
  },
}

export const defaultTheme: ThemeScheme = 'default'
export const defaultMode: ThemeMode = 'light'
