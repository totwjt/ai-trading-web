import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const DEV_UID = 'u_1001'
const UID_STORAGE_KEY = 'ai_trading_uid'

function resolveInitialUid(): string {
  const envUid = (import.meta as any).env?.VITE_DEFAULT_UID
  if (typeof envUid === 'string' && envUid.trim()) return envUid.trim()

  if (typeof window !== 'undefined') {
    const savedUid = window.localStorage.getItem(UID_STORAGE_KEY)
    if (savedUid?.trim()) return savedUid.trim()
  }

  return DEV_UID
}

export const useUserStore = defineStore('userStore', () => {
  const uid = ref(resolveInitialUid())

  const hasUser = computed(() => Boolean(uid.value.trim()))

  function setUid(nextUid: string) {
    const normalizedUid = nextUid.trim()
    uid.value = normalizedUid
    if (typeof window !== 'undefined') {
      if (normalizedUid) {
        window.localStorage.setItem(UID_STORAGE_KEY, normalizedUid)
      } else {
        window.localStorage.removeItem(UID_STORAGE_KEY)
      }
    }
  }

  return {
    uid,
    hasUser,
    setUid
  }
})
