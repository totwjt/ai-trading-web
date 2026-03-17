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
    <!-- 顶部导航栏 - 按照设计文件 -->
    <header class="flex items-center justify-between px-6 h-14 border-b border-slate-200 bg-white shrink-0">
      <div class="flex items-center space-x-8 h-full">
        <div class="flex items-center h-full">
          <button class="h-full px-4 text-sm font-bold active-tab">编辑策略</button>
          <button 
            class="h-full px-4 text-sm font-medium text-slate-500 hover:text-primary transition-colors"
            @click="runBacktest"
          >
            回测详情
          </button>
        </div>
        <div class="h-6 w-px bg-slate-200"></div>
        <span class="text-sm font-medium text-slate-600">策略: {{ strategyData.name }}</span>
      </div>
      <div class="flex items-center space-x-4">
        <!-- Backtesting Parameters -->
        <div class="flex items-center space-x-3 bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200 mr-2">
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
        <button class="bg-primary text-white px-5 py-1.5 rounded text-sm font-semibold hover:bg-blue-700 shadow-sm shadow-blue-200 transition-all" @click="runBacktest">
          运行回测
        </button>
        <button class="border border-slate-200 px-5 py-1.5 rounded text-sm font-medium hover:bg-slate-50 transition-colors" @click="saveStrategy">
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
        <div class="flex-1 overflow-auto editor-scrollbar font-mono text-[13px] leading-relaxed p-4 bg-[#1E1E1E]">
          <div class="flex">
            <div class="w-10 text-slate-600 select-none text-right pr-4">
              1<br/>2<br/>3<br/>4<br/>5<br/>6<br/>7<br/>8<br/>9<br/>10<br/>11<br/>12<br/>13<br/>14<br/>15<br/>16<br/>17<br/>18<br/>19<br/>20
            </div>
            <div class="flex-1 text-slate-300">
              <span class="text-pink-400 italic">import</span> pandas <span class="text-pink-400 italic">as</span> pd<br/>
              <span class="text-pink-400 italic">from</span> gzt_api <span class="text-pink-400 italic">import</span> Strategy, Order<br/><br/>
              <span class="text-blue-300">class</span> <span class="text-yellow-200">ValueStrategy</span>(<span class="text-green-300">Strategy</span>):<br/>
                  <span class="text-blue-300">def</span> <span class="text-yellow-200">on_init</span>(<span class="text-orange-300">self</span>):<br/>
                      <span class="text-slate-500"># 初始化沪深300权重股池</span><br/>
                      <span class="text-orange-300">self</span>.universe = [<span class="text-green-400">'000001.SH'</span>, <span class="text-green-400">'600519.SH'</span>]<br/>
                      <span class="text-orange-300">self</span>.set_benchmark(<span class="text-green-400">'000300.SH'</span>)<br/><br/>
                  <span class="text-blue-300">def</span> <span class="text-yellow-200">on_bar</span>(<span class="text-orange-300">self</span>, <span class="text-orange-300">bar</span>):<br/>
                      <span class="text-slate-500"># 简单的均线交叉逻辑</span><br/>
                      ma5 = <span class="text-orange-300">bar</span>.close.rolling(<span class="text-cyan-400">5</span>).mean()<br/>
                      ma20 = <span class="text-orange-300">bar</span>.close.rolling(<span class="text-cyan-400">20</span>).mean()<br/><br/>
                      <span class="text-pink-400 italic">if</span> ma5 &gt; ma20 <span class="text-pink-400 italic">and</span> <span class="text-orange-300">self</span>.pos == <span class="text-cyan-400">0</span>:<br/>
                          <span class="text-orange-300">self</span>.buy(<span class="text-orange-300">bar</span>.symbol, <span class="text-orange-300">bar</span>.close, <span class="text-cyan-400">1000</span>)<br/>
                      <span class="text-pink-400 italic">elif</span> ma5 &lt; ma20 <span class="text-pink-400 italic">and</span> <span class="text-orange-300">self</span>.pos &gt; <span class="text-cyan-400">0</span>:<br/>
                          <span class="text-orange-300">self</span>.sell(<span class="text-orange-300">bar</span>.symbol, <span class="text-orange-300">bar</span>.close, <span class="text-orange-300">self</span>.pos)<br/>
              <span class="text-slate-400 cursor-blink animate-pulse">|</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧：运行日志 + 回测预览 -->
      <section class="w-[40%] flex flex-col border-l border-slate-200 bg-slate-50 overflow-hidden">
        <!-- 运行日志 -->
        <div class="h-1/2 flex flex-col border-b border-slate-200">
          <div class="flex items-center justify-between px-4 py-2 bg-white border-b border-slate-200">
            <span class="text-xs font-bold text-slate-700 uppercase tracking-tight">运行日志 / 错误</span>
            <button class="text-slate-400 hover:text-slate-600">
              <Icon icon="mdi:delete" :size="16" />
            </button>
          </div>
          <div class="flex-1 overflow-auto custom-scrollbar p-4 font-mono text-[12px] space-y-2">
            <div class="flex text-slate-500">
              <span class="w-20 shrink-0">[10:04:22]</span>
              <span class="text-blue-600">INFO:</span>
              <span class="ml-2">初始化策略引擎完成...</span>
            </div>
            <div class="flex text-slate-500">
              <span class="w-20 shrink-0">[10:04:23]</span>
              <span class="text-blue-600">INFO:</span>
              <span class="ml-2">正在下载 000300.SH 历史行情数据 [2022-01-01 -&gt; 2023-12-31]</span>
            </div>
            <div class="flex text-slate-500">
              <span class="w-20 shrink-0">[10:04:25]</span>
              <span class="text-up font-medium">ERROR:</span>
              <span class="ml-2">模块 'talib' 未找到。请在策略配置中添加依赖。</span>
            </div>
            <div class="flex text-slate-500">
              <span class="w-20 shrink-0">[10:04:28]</span>
              <span class="text-blue-600">INFO:</span>
              <span class="ml-2 text-slate-700">开始运行回测预览...</span>
            </div>
          </div>
        </div>

        <!-- 实时回测预览 -->
        <div class="h-1/2 flex flex-col bg-white">
          <div class="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
            <span class="text-xs font-bold text-slate-700 uppercase tracking-tight">实时回测预览</span>
            <div class="flex items-center space-x-3">
              <span class="text-[10px] text-slate-400 flex items-center">
                <span class="w-2 h-2 rounded-full bg-primary mr-1"></span>权益曲线
              </span>
              <span class="text-[10px] text-slate-400 flex items-center">
                <span class="w-2 h-2 rounded-full bg-slate-300 mr-1"></span>基准
              </span>
            </div>
          </div>
          <div class="flex-1 relative p-2 overflow-hidden flex flex-col">
            <div class="flex-1 flex items-end justify-between space-x-[2px] opacity-80 mt-4 px-4">
              <div class="w-2 bg-slate-200 h-[30%]"></div>
              <div class="w-2 bg-slate-200 h-[35%]"></div>
              <div class="w-2 bg-slate-200 h-[32%]"></div>
              <div class="w-2 bg-up h-[45%]"></div>
              <div class="w-2 bg-up h-[55%]"></div>
              <div class="w-2 bg-down h-[40%]"></div>
              <div class="w-2 bg-up h-[60%]"></div>
              <div class="w-2 bg-up h-[75%]"></div>
              <div class="w-2 bg-down h-[65%]"></div>
              <div class="w-2 bg-up h-[80%]"></div>
              <div class="w-2 bg-up h-[90%]"></div>
            </div>
            <div class="absolute inset-0 flex items-center justify-center">
              <div class="bg-white/90 backdrop-blur-sm px-4 py-2 rounded-full border border-slate-200 shadow-md">
                <span class="text-xs text-slate-600 flex items-center font-medium">
                  <span class="w-3 h-3 animate-spin mr-2 text-primary"></span>
                  预览数据加载中...
                </span>
              </div>
            </div>
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