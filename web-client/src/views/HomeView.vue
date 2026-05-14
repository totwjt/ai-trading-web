<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import {
  getDtPool,
  getHotSearchList,
  getHsgtTop10,
  getIndexSpot,
  getZtPool
} from '@/api/market'
import type {
  DtPoolItem,
  HotSearchItem,
  HsgtTop10Item,
  HsgtTop10Response,
  IndexSpotItem,
  IndexSpotResponse,
  PoolResponse,
  ZtPoolItem
} from '@/api/market'

const loading = ref(false)
const errorMessage = ref('')
const hotSearch = ref<HotSearchItem[]>([])
const hsgtTop10 = ref<HsgtTop10Item[]>([])
const hsgtMeta = ref<Pick<HsgtTop10Response, 'trade_date' | 'count'> | null>(null)
const indexSpot = ref<IndexSpotItem[]>([])
const indexMeta = ref<Pick<IndexSpotResponse, 'update_time' | 'count'> | null>(null)
const ztPool = ref<ZtPoolItem[]>([])
const dtPool = ref<DtPoolItem[]>([])
const ztMeta = ref<Pick<PoolResponse<ZtPoolItem>, 'update_time' | 'count'> | null>(null)
const dtMeta = ref<Pick<PoolResponse<DtPoolItem>, 'update_time' | 'count'> | null>(null)

const hsgtShanghaiTop10 = computed(() =>
  hsgtTop10.value
    .filter(item => item.market_type === '1')
    .sort((left, right) => left.rank - right.rank)
    .slice(0, 10)
)

const hsgtShenzhenTop10 = computed(() =>
  hsgtTop10.value
    .filter(item => item.market_type === '3')
    .sort((left, right) => left.rank - right.rank)
    .slice(0, 10)
)

const hotSearchUpCount = computed(() =>
  hotSearch.value.filter(item => parseChangePercent(item.change_pct) > 0).length
)

const primaryIndex = computed(() =>
  indexSpot.value.find(item => item.code === 'sh000001' || item.name === '上证指数') ?? indexSpot.value[0] ?? null
)

const strongestZt = computed(() =>
  [...ztPool.value].sort((left, right) => right.continuous_count - left.continuous_count)[0] ?? null
)

const largestDtSeal = computed(() =>
  [...dtPool.value].sort((left, right) => right.seal_amount - left.seal_amount)[0] ?? null
)

const industryStats = computed(() => {
  const stats = new Map<string, { industry: string; zt: number; dt: number }>()

  ztPool.value.forEach(item => {
    const industry = item.industry || '未分类'
    const current = stats.get(industry) ?? { industry, zt: 0, dt: 0 }
    current.zt += 1
    stats.set(industry, current)
  })

  dtPool.value.forEach(item => {
    const industry = item.industry || '未分类'
    const current = stats.get(industry) ?? { industry, zt: 0, dt: 0 }
    current.dt += 1
    stats.set(industry, current)
  })

  return [...stats.values()]
    .sort((left, right) => right.zt + right.dt - (left.zt + left.dt))
    .slice(0, 8)
})

const ztDisplayList = computed(() => ztPool.value)

const dtDisplayList = computed(() => dtPool.value)

const hotSearchDisplayList = computed(() => hotSearch.value)

const hsgtTables = computed(() => [
  {
    title: '沪股通十大成交',
    count: hsgtShanghaiTop10.value.length,
    amount: hsgtShanghaiTop10.value.reduce((total, item) => total + (item.amount ?? 0), 0),
    rows: hsgtShanghaiTop10.value
  },
  {
    title: '深股通十大成交',
    count: hsgtShenzhenTop10.value.length,
    amount: hsgtShenzhenTop10.value.reduce((total, item) => total + (item.amount ?? 0), 0),
    rows: hsgtShenzhenTop10.value
  }
])

const summaryCards = computed(() => [
  {
    label: '热搜股票',
    value: `${hotSearch.value.length}`,
    suffix: '只',
    subText: `上涨 ${hotSearchUpCount.value} / 下跌 ${hotSearch.value.length - hotSearchUpCount.value}`,
    tone: 'primary'
  },
  {
    label: primaryIndex.value?.name ?? '主要指数',
    value: primaryIndex.value ? primaryIndex.value.latest_price.toFixed(2) : '--',
    suffix: '',
    subText: primaryIndex.value
      ? `${formatPercent(primaryIndex.value.change_pct)} · ${primaryIndex.value.change_amount > 0 ? '+' : ''}${primaryIndex.value.change_amount.toFixed(2)}`
      : '等待接口返回',
    tone: primaryIndex.value
      ? primaryIndex.value.change_pct >= 0 ? 'up' : 'down'
      : 'neutral'
  },
  {
    label: '涨停股池',
    value: `${ztMeta.value?.count ?? ztPool.value.length}`,
    suffix: '只',
    subText: strongestZt.value ? `${strongestZt.value.name} ${strongestZt.value.continuous_count}连板` : '暂无数据',
    tone: 'up'
  },
  {
    label: '跌停股池',
    value: `${dtMeta.value?.count ?? dtPool.value.length}`,
    suffix: '只',
    subText: largestDtSeal.value ? `${largestDtSeal.value.name} 封单${formatMoney(largestDtSeal.value.seal_amount)}` : '暂无数据',
    tone: 'down'
  }
])

function parseChangePercent(value: string): number {
  return Number(value.replace('%', '')) || 0
}

function formatPercent(value: number | string): string {
  if (typeof value === 'string') {
    return value
  }
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatMoney(value: number | null | undefined): string {
  if (!value) {
    return '--'
  }
  if (Math.abs(value) >= 100000000) {
    return `${(value / 100000000).toFixed(2)}亿`
  }
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(2)}万`
  }
  return value.toLocaleString('zh-CN')
}

function formatTime(value: string | null | undefined): string {
  if (!value) {
    return '--'
  }
  if (value.length === 6) {
    return `${value.slice(0, 2)}:${value.slice(2, 4)}:${value.slice(4, 6)}`
  }
  return value
}

async function loadHomeData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''

  const [hsgtResult, hotResult, indexResult, ztResult, dtResult] = await Promise.allSettled([
    getHsgtTop10(),
    getHotSearchList(),
    getIndexSpot(),
    getZtPool(),
    getDtPool()
  ])

  const failedMessages: string[] = []

  if (hsgtResult.status === 'fulfilled') {
    hsgtTop10.value = hsgtResult.value.data
    hsgtMeta.value = {
      trade_date: hsgtResult.value.trade_date,
      count: hsgtResult.value.count
    }
  } else {
    failedMessages.push('沪深股通')
    console.error('获取沪深股通数据失败:', hsgtResult.reason)
  }

  if (hotResult.status === 'fulfilled') {
    hotSearch.value = hotResult.value.data
  } else {
    failedMessages.push('热搜')
    console.error('获取热搜数据失败:', hotResult.reason)
  }

  if (indexResult.status === 'fulfilled') {
    indexSpot.value = indexResult.value.data
    indexMeta.value = {
      update_time: indexResult.value.update_time,
      count: indexResult.value.count
    }
  } else {
    failedMessages.push('指数')
    console.error('获取指数数据失败:', indexResult.reason)
  }

  if (ztResult.status === 'fulfilled') {
    ztPool.value = ztResult.value.data
    ztMeta.value = {
      update_time: ztResult.value.update_time,
      count: ztResult.value.count
    }
  } else {
    failedMessages.push('涨停池')
    console.error('获取涨停池数据失败:', ztResult.reason)
  }

  if (dtResult.status === 'fulfilled') {
    dtPool.value = dtResult.value.data
    dtMeta.value = {
      update_time: dtResult.value.update_time,
      count: dtResult.value.count
    }
  } else {
    failedMessages.push('跌停池')
    console.error('获取跌停池数据失败:', dtResult.reason)
  }

  if (failedMessages.length > 0) {
    errorMessage.value = `${failedMessages.join('、')}数据加载失败，请检查外部接口服务`
  }

  loading.value = false
}

onMounted(() => {
  loadHomeData()
})
</script>

<template>
  <div class="flex h-[calc(100vh-48px)] flex-col overflow-hidden bg-bgMain p-3 text-sm">
    <div class="mb-3 flex shrink-0 items-center justify-between rounded-lg border border-border bg-card px-4 py-3 shadow-sm">
      <div>
        <h1 class="text-lg font-bold text-textMain">市场首页</h1>
        <p class="mt-0.5 text-xs text-textMute">
          <span v-if="indexMeta?.update_time">指数更新 {{ indexMeta.update_time }}</span>
          <span v-if="indexMeta?.update_time && ztMeta?.update_time">，</span>
          <span v-if="ztMeta?.update_time">涨跌停更新 {{ ztMeta.update_time }}</span>
        </p>
      </div>
      <button
        class="rounded-md border border-border bg-bgMain px-3 py-1.5 text-xs font-medium text-textMain hover:border-primary hover:bg-primary/5 hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="loading"
        @click="loadHomeData"
      >
        {{ loading ? '刷新中' : '刷新数据' }}
      </button>
    </div>

    <div
      v-if="errorMessage"
      class="mb-3 rounded-lg border border-down/30 bg-down/5 px-3 py-2 text-xs text-down"
    >
      {{ errorMessage }}
    </div>

    <section class="mb-3 grid shrink-0 grid-cols-4 gap-3">
      <div
        v-for="card in summaryCards"
        :key="card.label"
        :class="[
          'relative overflow-hidden rounded-lg border border-border bg-card p-3 shadow-sm',
          'flex min-h-[82px] justify-between gap-3',
          card.tone === 'up' ? 'before:bg-up' : '',
          card.tone === 'down' ? 'before:bg-down' : '',
          card.tone === 'primary' ? 'before:bg-primary' : '',
          card.tone === 'neutral' ? 'before:bg-border' : '',
          'before:absolute before:left-0 before:top-0 before:h-full before:w-1'
        ]"
      >
        <div class="min-w-0 pl-1">
          <p class="text-xs text-textMute mb-1">{{ card.label }}</p>
          <p
            :class="[
              'font-numeric text-xl font-bold leading-tight',
              card.tone === 'up' ? 'text-up' : '',
              card.tone === 'down' ? 'text-down' : '',
              card.tone === 'primary' ? 'text-primary' : '',
              card.tone === 'neutral' ? 'text-textMain' : ''
            ]"
          >
            {{ card.value }}<span v-if="card.suffix" class="ml-1 text-sm text-textSub">{{ card.suffix }}</span>
          </p>
        </div>
        <span class="max-w-36 self-end text-right text-xs leading-5 text-textMute">{{ card.subText }}</span>
      </div>
    </section>

    <div class="grid min-h-0 flex-1 grid-cols-12 gap-3">
      <div class="col-span-9 flex min-h-0 flex-col gap-3">
        <div class="grid min-h-0 flex-[1.05] grid-cols-2 gap-3">
          <div
            v-for="table in hsgtTables"
            :key="table.title"
            class="panel flex min-h-0 flex-col overflow-hidden"
          >
            <div class="panel-header">
              <div class="flex items-center space-x-3">
                <span class="font-bold text-textMain">{{ table.title }}</span>
                <span class="text-xs text-textMute">{{ table.count }} 条</span>
              </div>
              <span class="text-xs text-textMute">成交额 {{ formatMoney(table.amount) }}</span>
            </div>
            <div class="scroll-area min-h-0 flex-1 overflow-auto">
              <table class="w-full density-table">
                <thead class="sticky top-0 z-10 border-b border-border bg-bgMain text-textMute">
                  <tr>
                    <th class="text-left">排名</th>
                    <th class="text-left">股票</th>
                    <th class="text-right">收盘价</th>
                    <th class="text-right">涨跌额</th>
                    <th class="text-right">成交额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loading && table.rows.length === 0">
                    <td colspan="5" class="text-center text-textMute">正在加载...</td>
                  </tr>
                  <tr
                    v-for="item in table.rows"
                    :key="`${item.market_type}-${item.rank}-${item.ts_code}`"
                    class="border-b border-border/70 hover:bg-primary/5"
                  >
                    <td class="font-numeric text-textMute">
                      <span class="inline-flex h-5 min-w-5 items-center justify-center rounded bg-bgMain px-1">{{ item.rank }}</span>
                    </td>
                    <td>
                      <p class="font-medium text-textMain">{{ item.name }}</p>
                      <p class="font-numeric text-xxs text-textMute">{{ item.ts_code }}</p>
                    </td>
                    <td class="text-right font-numeric text-textMain">{{ item.close.toFixed(2) }}</td>
                    <td
                      :class="[
                        'text-right font-numeric',
                        item.change >= 0 ? 'text-up' : 'text-down'
                      ]"
                    >
                      {{ item.change > 0 ? '+' : '' }}{{ item.change.toFixed(2) }}
                    </td>
                    <td class="text-right font-numeric text-textSub">{{ formatMoney(item.amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="grid min-h-0 flex-1 grid-cols-2 gap-3">
          <div class="panel flex min-h-0 flex-col overflow-hidden">
            <div class="panel-header">
              <h3 class="font-bold text-textMain">涨停股池</h3>
              <span class="text-xs text-textMute">{{ ztMeta?.update_time || '--' }}</span>
            </div>
            <div class="scroll-area min-h-0 flex-1 overflow-auto">
              <table class="w-full density-table">
                <thead class="sticky top-0 z-10 border-b border-border bg-bgMain text-textMute">
                  <tr>
                    <th class="text-left">股票</th>
                    <th class="text-right">涨幅</th>
                    <th class="text-right">连板</th>
                    <th class="text-right">封单</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loading && ztPool.length === 0">
                    <td colspan="4" class="text-center text-textMute">正在加载...</td>
                  </tr>
                  <tr
                    v-for="item in ztDisplayList"
                    :key="item.ts_code"
                    class="border-b border-border/70 hover:bg-up/5"
                  >
                    <td>
                      <p class="font-medium text-textMain">{{ item.name }}</p>
                      <p class="font-numeric text-xxs text-textMute">{{ item.ts_code }} · {{ item.industry || '--' }}</p>
                    </td>
                    <td class="text-right font-numeric text-up">{{ formatPercent(item.change_pct) }}</td>
                    <td class="text-right font-numeric text-textSub">{{ item.continuous_count }}</td>
                    <td class="text-right font-numeric text-textSub">{{ formatMoney(item.seal_amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="panel flex min-h-0 flex-col overflow-hidden">
            <div class="panel-header">
              <h3 class="font-bold text-textMain">跌停股池</h3>
              <span class="text-xs text-textMute">{{ dtMeta?.update_time || '--' }}</span>
            </div>
            <div class="scroll-area min-h-0 flex-1 overflow-auto">
              <table class="w-full density-table">
                <thead class="sticky top-0 z-10 border-b border-border bg-bgMain text-textMute">
                  <tr>
                    <th class="text-left">股票</th>
                    <th class="text-right">跌幅</th>
                    <th class="text-right">连续跌停</th>
                    <th class="text-right">封单</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loading && dtPool.length === 0">
                    <td colspan="4" class="text-center text-textMute">正在加载...</td>
                  </tr>
                  <tr
                    v-for="item in dtDisplayList"
                    :key="item.ts_code"
                    class="border-b border-border/70 hover:bg-down/5"
                  >
                    <td>
                      <p class="font-medium text-textMain">{{ item.name }}</p>
                      <p class="font-numeric text-xxs text-textMute">{{ item.ts_code }} · {{ item.industry || '--' }}</p>
                    </td>
                    <td class="text-right font-numeric text-down">{{ formatPercent(item.change_pct) }}</td>
                    <td class="text-right font-numeric text-textSub">{{ item.continuous_days }}</td>
                    <td class="text-right font-numeric text-textSub">{{ formatMoney(item.seal_amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="col-span-3 flex min-h-0 flex-col gap-3">
        <div class="panel flex min-h-0 flex-[1.4] flex-col p-3">
          <div class="mb-2 flex shrink-0 items-center justify-between">
            <h3 class="font-bold text-textMain">热搜股票</h3>
            <span class="text-xs text-textMute">{{ hotSearch.length }}只</span>
          </div>
          <div class="scroll-area min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1">
            <div v-if="loading && hotSearch.length === 0" class="py-6 text-center text-xs text-textMute">
              正在加载...
            </div>
            <div
              v-for="(item, index) in hotSearchDisplayList"
              :key="`${item.symbol}-${item.name_code}`"
              class="flex items-center justify-between rounded-md border border-transparent px-2 py-1.5 hover:border-border hover:bg-bgMain"
            >
              <div class="min-w-0">
                <p class="truncate text-xs font-medium text-textMain">
                  <span class="mr-2 inline-flex h-4 min-w-4 items-center justify-center rounded bg-bgMain font-numeric text-xxs text-textMute">{{ index + 1 }}</span>{{ item.name_code }}
                </p>
                <p class="mt-0.5 text-xxs text-textMute">{{ item.symbol }} · 热度 {{ item.hot_score.toLocaleString('zh-CN') }}</p>
              </div>
              <span
                :class="[
                  'ml-2 font-numeric text-xs font-semibold',
                  parseChangePercent(item.change_pct) >= 0 ? 'text-up' : 'text-down'
                ]"
              >
                {{ item.change_pct }}
              </span>
            </div>
          </div>
        </div>

        <div class="panel flex min-h-0 flex-1 flex-col p-3">
          <div class="mb-2 flex shrink-0 items-center justify-between">
            <h3 class="font-bold text-textMain">行业异动</h3>
            <span class="text-xs text-textMute">涨跌停统计</span>
          </div>
          <div class="scroll-area min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1">
            <div v-if="loading && industryStats.length === 0" class="py-6 text-center text-xs text-textMute">
              正在加载...
            </div>
            <div
              v-for="item in industryStats"
              :key="item.industry"
              class="flex items-center justify-between rounded-md px-2 py-1.5 text-xs hover:bg-bgMain"
            >
              <span class="truncate text-textSub">{{ item.industry }}</span>
              <span class="ml-2 flex items-center space-x-2 font-numeric">
                <span class="text-up">{{ item.zt }}</span>
                <span class="text-textMute">/</span>
                <span class="text-down">{{ item.dt }}</span>
              </span>
            </div>
          </div>
        </div>

        <div class="panel shrink-0 p-3">
          <h3 class="mb-2 font-bold text-textMain">封板观察</h3>
          <dl class="space-y-2 text-xs">
            <div class="flex justify-between">
              <dt class="text-textMute">最强连板</dt>
              <dd class="font-medium text-textMain">{{ strongestZt?.name || '--' }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-textMute">最后封板</dt>
              <dd class="font-numeric text-textSub">{{ formatTime(strongestZt?.last_seal_time) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-textMute">跌停最大封单</dt>
              <dd class="font-medium text-textMain">{{ largestDtSeal?.name || '--' }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-textMute">封单金额</dt>
              <dd class="font-numeric text-textSub">{{ formatMoney(largestDtSeal?.seal_amount) }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  border: 1px solid theme('colors.border');
  border-radius: 0.5rem;
  background: theme('colors.card');
  box-shadow: 0 1px 2px rgb(0 0 0 / 0.05);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  border-bottom: 1px solid theme('colors.border');
  padding: 0.625rem 1rem;
  background: theme('colors.bgMain');
}

.scroll-area {
  scrollbar-width: thin;
  scrollbar-color: theme('colors.border') transparent;
}

.scroll-area::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.scroll-area::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: theme('colors.border');
}

.scroll-area::-webkit-scrollbar-track {
  background: transparent;
}
</style>
