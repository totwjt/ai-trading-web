<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 获取策略ID
const strategyId = route.params.id

// 模拟策略数据
const strategyData = ref({
  name: '沪深300价值增强-V2',
  type: '指数增强',
  status: '运行中'
})

// 返回策略中心
const goBack = () => {
  router.push('/backtest')
}

// 保存策略
const saveStrategy = () => {
  console.log('保存策略')
}

// 运行回测
const runBacktest = () => {
  if (strategyId) {
    router.push(`/backtest/detail/${strategyId}`)
  } else {
    // 新建策略时，先保存再跳转
    console.log('保存并运行回测')
  }
}
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col overflow-hidden">
    <!-- 顶部导航栏 -->
    <header class="flex items-center justify-between px-6 h-12 border-b border-slate-200 bg-white shrink-0">
      <div class="flex items-center space-x-4">
        <button 
          class="flex items-center gap-1 text-sm text-slate-600 hover:text-primary transition-colors"
          @click="goBack"
        >
          <Icon icon="mdi:arrow-left" :size="20" />
          返回策略列表
        </button>
        <div class="h-4 w-px bg-slate-200"></div>
        <span class="text-sm font-medium text-slate-600">编辑策略: {{ strategyData.name }}</span>
      </div>
      <div class="flex items-center space-x-4">
        <!-- Backtesting Parameters -->
        <div class="flex items-center space-x-3 bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200">
          <div class="flex items-center space-x-1.5">
            <label class="text-[11px] text-slate-500 whitespace-nowrap">开始日期</label>
            <input class="bg-transparent border-none p-0 text-xs focus:ring-0 w-24 text-slate-700" type="date" value="2023-01-01"/>
          </div>
          <div class="w-px h-3 bg-slate-300"></div>
          <div class="flex items-center space-x-1.5">
            <label class="text-[11px] text-slate-500 whitespace-nowrap">结束日期</label>
            <input class="bg-transparent border-none p-0 text-xs focus:ring-0 w-24 text-slate-700" type="date" value="2023-12-31"/>
          </div>
          <div class="w-px h-3 bg-slate-300"></div>
          <div class="flex items-center space-x-1.5">
            <label class="text-[11px] text-slate-500 whitespace-nowrap">数据频率</label>
            <select class="bg-transparent border-none p-0 text-xs focus:ring-0 text-slate-700 cursor-pointer">
              <option>日线</option>
              <option>周线</option>
              <option>1分钟</option>
              <option>5分钟</option>
              <option>15分钟</option>
            </select>
          </div>
        </div>
        <button class="bg-primary text-white px-4 py-1.5 rounded text-sm font-semibold hover:bg-blue-700 shadow-sm shadow-blue-200 transition-all" @click="runBacktest">
          运行回测
        </button>
        <button class="border border-slate-200 px-4 py-1.5 rounded text-sm font-medium hover:bg-slate-50 transition-colors" @click="saveStrategy">
          保存
        </button>
      </div>
    </header>

    <!-- 主编辑区域 -->
    <main class="flex-1 flex overflow-hidden">
      <!-- 左侧：代码编辑器 -->
      <section class="w-[60%] bg-editor flex flex-col relative" data-purpose="code-editor-container">
        <div class="flex items-center justify-between px-4 py-2 border-b border-white/10 text-xs text-slate-400 bg-[#252526]">
          <span class="flex items-center">
            <span class="w-2 h-2 rounded-full bg-orange-400 mr-2"></span>
            main.py
          </span>
          <span>Python 3.8</span>
        </div>
        <div class="flex-1 bg-[#1E1E1E] p-4 font-mono text-sm text-slate-300 overflow-auto">
          <pre><code>
# 双均线交叉策略
class DualMovingAverageCross(bt.Strategy):
    params = (
        ('short_period', 5),
        ('long_period', 20),
    )

    def __init__(self):
        self.short_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period
        )
        self.long_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period
        )
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()
          </code></pre>
        </div>
      </section>

      <!-- 右侧：参数配置 -->
      <section class="w-[40%] border-l border-slate-200 bg-white flex flex-col overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-200 bg-slate-50">
          <h3 class="font-bold text-sm">策略参数配置</h3>
        </div>
        <div class="flex-1 overflow-auto p-4 space-y-4">
          <div>
            <label class="text-xs text-slate-500 block mb-1">策略名称</label>
            <input 
              type="text" 
              v-model="strategyData.name"
              class="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
          <div>
            <label class="text-xs text-slate-500 block mb-1">短期均线周期</label>
            <input 
              type="number" 
              value="5"
              class="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
          <div>
            <label class="text-xs text-slate-500 block mb-1">长期均线周期</label>
            <input 
              type="number" 
              value="20"
              class="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
          <div>
            <label class="text-xs text-slate-500 block mb-1">初始资金</label>
            <input 
              type="number" 
              value="1000000"
              class="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
        </div>
      </section>
    </main>

    <!-- 底部状态栏 -->
    <footer class="bg-white border-t border-slate-200 px-4 py-1.5 flex items-center justify-between text-[10px] text-slate-400 font-medium">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span> Python 环境正常
        </span>
        <span>Backtrader v1.9.78.123</span>
      </div>
      <div>
        Line 15, Column 25
      </div>
    </footer>
  </div>
</template>

<style scoped>
.active-tab {
  border-bottom: 2px solid #0066FF;
  color: #0066FF;
}
</style>