<script setup lang="ts">
import { ref } from 'vue'

// 模拟资产数据
const assets = ref([
  { label: '总资产 (CNY)', value: '1,248,500.00' },
  { label: '今日盈亏', value: '+15,240.50', change: '+1.24%' },
  { label: '持仓市值', value: '842,300.00' },
  { label: '模拟账户余额', value: '406,200.00' }
])

// 模拟策略数据
const strategies = ref([
  {
    id: 1,
    name: '中证500增强A1',
    returns: '+12.4%',
    winRate: '68.5%',
    maxDrawdown: '4.2%'
  },
  {
    id: 2,
    name: '均线回归Alpha',
    returns: '-2.1%',
    winRate: '52.3%',
    maxDrawdown: '8.7%'
  },
  {
    id: 3,
    name: '高频套利V2',
    returns: '+4.8%',
    winRate: '81.0%',
    maxDrawdown: '1.5%'
  }
])
</script>

<template>
  <div class="min-h-screen bg-bgMain p-4">
    <!-- Top Summary Bar -->
    <section class="grid grid-cols-4 gap-4 mb-4">
      <div 
        v-for="(asset, index) in assets"
        :key="index"
        class="bg-card p-4 rounded-lg shadow-sm border border-border flex justify-between items-end"
      >
        <div>
          <p class="text-xs text-textMute mb-1">{{ asset.label }}</p>
          <p class="text-2xl font-bold font-numeric">{{ asset.value }}</p>
        </div>
        <span v-if="asset.change" class="text-sm font-semibold text-up">{{ asset.change }}</span>
      </div>
    </section>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-12 gap-4">
      <!-- Central Chart Section -->
      <div class="col-span-9 space-y-4">
        <!-- K线图区域 -->
        <div class="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2 border-b border-border">
            <div class="flex items-center space-x-4">
              <span class="font-bold text-lg text-textMain">贵州茅台 (600519.SH)</span>
              <div class="flex space-x-2 text-xs">
                <span class="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 text-textSub">分时</span>
                <span class="bg-primary text-white px-2 py-1 rounded cursor-pointer">日K</span>
                <span class="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 text-textSub">周K</span>
              </div>
            </div>
            <div class="flex items-center space-x-4 text-xs text-textMute">
              <span class="cursor-pointer hover:text-primary">MA</span>
              <span class="cursor-pointer hover:text-primary">MACD</span>
              <span class="cursor-pointer hover:text-primary">KDJ</span>
              <span class="cursor-pointer hover:text-primary">BOLL</span>
            </div>
          </div>
          <!-- Chart Container -->
          <div class="chart-container relative p-4 bg-card h-64 flex items-center justify-center text-textMute">
            K线图区域 (Canvas)
          </div>
        </div>

        <!-- Strategy Management -->
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-card rounded-lg shadow-sm border border-border">
            <div class="px-4 py-3 border-b border-border flex justify-between items-center">
              <h3 class="font-bold text-sm text-textMain">策略管理</h3>
              <button class="text-xs text-primary hover:underline">查看更多</button>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full density-table">
                <thead class="bg-gray-50 dark:bg-gray-800 text-textMute">
                  <tr>
                    <th class="text-left">策略名称</th>
                    <th class="text-right">当前收益</th>
                    <th class="text-right">胜率</th>
                    <th class="text-right">最大回撤</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="strategy in strategies"
                    :key="strategy.id"
                    class="hover:bg-primary/5"
                  >
                    <td class="font-medium text-textMain">{{ strategy.name }}</td>
                    <td 
                      :class="[
                        'text-right font-numeric',
                        strategy.returns.startsWith('+') ? 'text-up' : 'text-down'
                      ]"
                    >
                      {{ strategy.returns }}
                    </td>
                    <td class="text-right font-numeric text-textSub">{{ strategy.winRate }}</td>
                    <td class="text-right font-numeric text-textSub">{{ strategy.maxDrawdown }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="bg-card rounded-lg shadow-sm border border-border p-4">
            <h3 class="font-bold text-sm text-textMain mb-4">快速操作</h3>
            <div class="grid grid-cols-2 gap-3">
              <button class="px-4 py-3 bg-up text-white text-sm font-bold rounded hover:opacity-90 transition-opacity">
                买入
              </button>
              <button class="px-4 py-3 bg-down text-white text-sm font-bold rounded hover:opacity-90 transition-opacity">
                卖出
              </button>
              <button class="px-4 py-2 border border-border text-textMain text-sm font-bold rounded hover:bg-primary/5 transition-colors">
                查看持仓
              </button>
              <button class="px-4 py-2 border border-border text-textMain text-sm font-bold rounded hover:bg-primary/5 transition-colors">
                策略回测
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel -->
      <div class="col-span-3 space-y-4">
        <!-- Market News -->
        <div class="bg-card rounded-lg shadow-sm border border-border p-4">
          <h3 class="font-bold text-sm text-textMain mb-3">市场动态</h3>
          <div class="space-y-3">
            <div class="text-xs">
              <p class="font-medium text-textMain">A股三大指数集体收涨</p>
              <p class="text-textMute mt-1">沪指涨1.2%，深成指涨1.5%，创业板指涨2.1%</p>
            </div>
            <div class="text-xs">
              <p class="font-medium text-textMain">北向资金净流入</p>
              <p class="text-textMute mt-1">今日净流入85.6亿元</p>
            </div>
            <div class="text-xs">
              <p class="font-medium text-textMain">新能源板块领涨</p>
              <p class="text-textMute mt-1">光伏、锂电池概念股表现强势</p>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="bg-card rounded-lg shadow-sm border border-border p-4">
          <h3 class="font-bold text-sm text-textMain mb-3">市场概览</h3>
          <div class="space-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-textMute">上涨股票</span>
              <span class="text-up font-bold">1,856</span>
            </div>
            <div class="flex justify-between">
              <span class="text-textMute">下跌股票</span>
              <span class="text-down font-bold">1,234</span>
            </div>
            <div class="flex justify-between">
              <span class="text-textMute">涨停股票</span>
              <span class="text-up font-bold">78</span>
            </div>
            <div class="flex justify-between">
              <span class="text-textMute">跌停股票</span>
              <span class="text-down font-bold">12</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  min-height: 400px;
}
</style>