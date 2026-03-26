<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getSystemStatus } from '@/api/trading'

const POLL_INTERVAL = 3000

const isConnected = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

const fetchStatus = async () => {
  try {
    const newStatus = await getSystemStatus()
    if (isConnected.value !== newStatus) {
      isConnected.value = newStatus
    }
  } catch {
    if (isConnected.value !== false) {
      isConnected.value = false
    }
  }
}

onMounted(() => {
  fetchStatus()
  timer = setInterval(fetchStatus, POLL_INTERVAL)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="flex items-center gap-1.5 text-xs">
    <template v-if="isConnected">
      <span class="w-2 h-2 rounded-full bg-green-400"></span>
      <span class="text-green-400">系统已连接</span>
    </template>
    <template v-else>
      <span class="w-2 h-2 rounded-full bg-red-500"></span>
      <span class="text-red-400">系统已断开</span>
    </template>
  </div>
</template>
