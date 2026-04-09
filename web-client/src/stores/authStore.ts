import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { UserProfile } from '@/api/auth'

const ACCESS_TOKEN_KEY = 'ai_trading_access_token'
const REFRESH_TOKEN_KEY = 'ai_trading_refresh_token'
const AUTH_USER_KEY = 'ai_trading_auth_user'
const AUTH_PERMISSIONS_KEY = 'ai_trading_permissions'

function getLocalStorageItem(key: string): string {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem(key) || ''
}

function parseUserProfile(raw: string): UserProfile | null {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as UserProfile
    return parsed?.id ? parsed : null
  } catch {
    return null
  }
}

function parsePermissions(raw: string): string[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === 'string') : []
  } catch {
    return []
  }
}

export const useAuthStore = defineStore('authStore', () => {
  const accessToken = ref(getLocalStorageItem(ACCESS_TOKEN_KEY))
  const refreshToken = ref(getLocalStorageItem(REFRESH_TOKEN_KEY))
  const user = ref<UserProfile | null>(parseUserProfile(getLocalStorageItem(AUTH_USER_KEY)))
  const permissions = ref<string[]>(parsePermissions(getLocalStorageItem(AUTH_PERMISSIONS_KEY)))

  const isAuthenticated = computed(() => Boolean(accessToken.value && user.value))

  function setSession(payload: {
    accessToken: string
    refreshToken: string
    user: UserProfile
    permissions?: string[]
  }) {
    accessToken.value = payload.accessToken
    refreshToken.value = payload.refreshToken
    user.value = payload.user
    permissions.value = payload.permissions || []

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken.value)
      window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken.value)
      window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user.value))
      window.localStorage.setItem(AUTH_PERMISSIONS_KEY, JSON.stringify(permissions.value))
    }
  }

  function clearSession() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    permissions.value = []

    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY)
      window.localStorage.removeItem(REFRESH_TOKEN_KEY)
      window.localStorage.removeItem(AUTH_USER_KEY)
      window.localStorage.removeItem(AUTH_PERMISSIONS_KEY)
    }
  }

  function hasPermission(permission: string): boolean {
    if (!permission) return true
    return permissions.value.includes(permission)
  }

  return {
    accessToken,
    refreshToken,
    user,
    permissions,
    isAuthenticated,
    setSession,
    clearSession,
    hasPermission
  }
})
