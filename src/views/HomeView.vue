<script setup lang="ts">
import { ref } from 'vue'

const message = ref('欢迎使用 AI 股票交易平台')
</script>

<template>
  <div class="min-h-screen bg-bgMain p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-2xl font-bold text-textMain mb-4">{{ message }}</h1>
      <p class="text-textSub">这是一个 AI 驱动的股票交易平台</p>
    </div>
  </div>
</template>
