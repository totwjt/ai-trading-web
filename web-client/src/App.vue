<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'
import SimpleLayout from '@/components/layout/SimpleLayout.vue'

const route = useRoute()
const layoutComponent = computed(() => {
  return route.meta.layout === 'simple' ? SimpleLayout : MainLayout
})
</script>

<template>
  <component :is="layoutComponent" />
</template>

<style scoped>
</style>
