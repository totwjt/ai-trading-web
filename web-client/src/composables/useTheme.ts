import { ref, computed } from 'vue'
import { themes, defaultTheme, defaultMode, type ThemeScheme, type ThemeMode } from '@/config/theme'

const STORAGE_KEY = 'theme_config'

function loadFromStorage(): { scheme: ThemeScheme; mode: ThemeMode } {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return {
        scheme: parsed.scheme || defaultTheme,
        mode: parsed.mode || defaultMode
      }
    }
  } catch {}
  return { scheme: defaultTheme, mode: defaultMode }
}

function saveToStorage(scheme: ThemeScheme, mode: ThemeMode) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ scheme, mode }))
}

const currentScheme = ref<ThemeScheme>(loadFromStorage().scheme)
const currentMode = ref<ThemeMode>(loadFromStorage().mode)

function hexToRgb(hex: string): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result 
    ? `${parseInt(result[1], 16)} ${parseInt(result[2], 16)} ${parseInt(result[3], 16)}`
    : '0 0 0'
}

function applyTheme(scheme: ThemeScheme, mode: ThemeMode) {
  const colors = themes[scheme].colors[mode]
  const root = document.documentElement
  
  root.style.setProperty('--color-primary', hexToRgb(colors.primary))
  root.style.setProperty('--color-up', hexToRgb(colors.up))
  root.style.setProperty('--color-down', hexToRgb(colors.down))
  root.style.setProperty('--color-border', hexToRgb(colors.border))
  root.style.setProperty('--color-bg-main', hexToRgb(colors.bgMain))
  root.style.setProperty('--color-card', hexToRgb(colors.card))
  root.style.setProperty('--color-text-main', hexToRgb(colors.textMain))
  root.style.setProperty('--color-text-sub', hexToRgb(colors.textSub))
  root.style.setProperty('--color-text-mute', hexToRgb(colors.textMute))
  
  if (mode === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

applyTheme(currentScheme.value, currentMode.value)

export function useTheme() {
  const currentColors = computed(() => 
    themes[currentScheme.value].colors[currentMode.value]
  )

  const setScheme = (scheme: ThemeScheme) => {
    currentScheme.value = scheme
    saveToStorage(scheme, currentMode.value)
    applyTheme(scheme, currentMode.value)
  }

  const setMode = (mode: ThemeMode) => {
    currentMode.value = mode
    saveToStorage(currentScheme.value, mode)
    applyTheme(currentScheme.value, mode)
  }

  const toggleMode = () => {
    setMode(currentMode.value === 'light' ? 'dark' : 'light')
  }

  return {
    scheme: currentScheme,
    mode: currentMode,
    colors: currentColors,
    setScheme,
    setMode,
    toggleMode,
    themes
  }
}
