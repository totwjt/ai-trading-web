export type ThemeMode = 'light' | 'dark'
export type ThemeScheme = 'default' | 'ocean' | 'forest'

export interface ThemeColors {
  primary: string
  up: string
  down: string
  border: string
  bgMain: string
  card: string
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
        primary: '#0066FF',
        up: '#FF0000',
        down: '#00B050',
        border: '#E5E7EB',
        bgMain: '#F9FAFB',
        card: '#FFFFFF',
        textMain: '#1F2937',
        textSub: '#6B7280',
        textMute: '#9CA3AF',
      },
      dark: {
        primary: '#3B82F6',
        up: '#EF4444',
        down: '#22C55E',
        border: '#374151',
        bgMain: '#111827',
        card: '#1F2937',
        textMain: '#F9FAFB',
        textSub: '#9CA3AF',
        textMute: '#6B7280',
      },
    },
  },
  ocean: {
    name: '海洋',
    colors: {
      light: {
        primary: '#0891B2',
        up: '#DC2626',
        down: '#059669',
        border: '#CBD5E1',
        bgMain: '#F0F9FF',
        card: '#FFFFFF',
        textMain: '#0F172A',
        textSub: '#475569',
        textMute: '#94A3B8',
      },
      dark: {
        primary: '#06B6D4',
        up: '#F87171',
        down: '#34D399',
        border: '#334155',
        bgMain: '#0C1929',
        card: '#1E293B',
        textMain: '#F1F5F9',
        textSub: '#94A3B8',
        textMute: '#64748B',
      },
    },
  },
  forest: {
    name: '森林',
    colors: {
      light: {
        primary: '#059669',
        up: '#DC2626',
        down: '#2563EB',
        border: '#D1D5DB',
        bgMain: '#F6F5F3',
        card: '#FFFFFF',
        textMain: '#1C1917',
        textSub: '#57534E',
        textMute: '#A8A29E',
      },
      dark: {
        primary: '#10B981',
        up: '#F87171',
        down: '#60A5FA',
        border: '#3F3F46',
        bgMain: '#1C1917',
        card: '#292524',
        textMain: '#FAFAF9',
        textSub: '#A8A29E',
        textMute: '#78716C',
      },
    },
  },
}

export const defaultTheme: ThemeScheme = 'default'
export const defaultMode: ThemeMode = 'light'
