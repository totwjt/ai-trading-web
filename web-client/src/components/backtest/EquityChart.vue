<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ColorType, createChart, LineStyle, type IChartApi, type ISeriesApi, type LineData } from 'lightweight-charts'
import type { EquityPoint } from '@/api/backtest'

const props = defineProps<{
  data: EquityPoint[]
  benchmark?: string
}>()

const chartRef = ref<HTMLDivElement | null>(null)

let chart: IChartApi | null = null
let equitySeries: ISeriesApi<'Line'> | null = null
let benchmarkSeries: ISeriesApi<'Line'> | null = null
let resizeObserver: ResizeObserver | null = null

function toLineData(values: EquityPoint[], key: 'equity' | 'benchmark'): LineData[] {
  return values.map((item) => ({
    time: item.date as LineData['time'],
    value: item[key]
  }))
}

function updateChartData() {
  if (!equitySeries || !benchmarkSeries) return

  equitySeries.setData(toLineData(props.data, 'equity'))
  benchmarkSeries.setData(toLineData(props.data, 'benchmark'))
}

function initChart() {
  if (!chartRef.value || chart) return

  chart = createChart(chartRef.value, {
    autoSize: true,
    layout: {
      background: { type: ColorType.Solid, color: '#FFFFFF' },
      textColor: '#6B7280',
      fontSize: 11
    },
    grid: {
      vertLines: { color: '#EEF2F7' },
      horzLines: { color: '#EEF2F7' }
    },
    rightPriceScale: {
      borderColor: '#E5E7EB'
    },
    timeScale: {
      borderColor: '#E5E7EB',
      timeVisible: true,
      secondsVisible: false,
      rightOffset: 4,
      barSpacing: 8
    },
    crosshair: {
      vertLine: {
        color: '#CBD5E1',
        style: LineStyle.Dashed
      },
      horzLine: {
        color: '#CBD5E1',
        style: LineStyle.Dashed
      }
    },
    localization: {
      locale: 'zh-CN'
    }
  })

  equitySeries = chart.addLineSeries({
    color: '#FF0000',
    lineWidth: 2,
    title: '本策略收益',
    lastValueVisible: true,
    priceLineVisible: false
  })

  benchmarkSeries = chart.addLineSeries({
    color: '#0066FF',
    lineWidth: 2,
    lineStyle: LineStyle.Dashed,
    title: props.benchmark || '沪深300基准',
    lastValueVisible: true,
    priceLineVisible: false
  })

  updateChartData()
  chart.timeScale().fitContent()

  resizeObserver = new ResizeObserver(() => {
    if (!chartRef.value || !chart) return
    chart.applyOptions({
      width: chartRef.value.clientWidth,
      height: chartRef.value.clientHeight
    })
  })

  resizeObserver.observe(chartRef.value)
}

function destroyChart() {
  resizeObserver?.disconnect()
  resizeObserver = null
  benchmarkSeries = null
  equitySeries = null
  chart?.remove()
  chart = null
}

onMounted(() => {
  initChart()
})

onBeforeUnmount(() => {
  destroyChart()
})

watch(
  () => props.data,
  () => {
    if (!chart) {
      initChart()
      return
    }

    updateChartData()
    chart.timeScale().fitContent()
  },
  { deep: true }
)

watch(
  () => props.benchmark,
  (value) => {
    if (!benchmarkSeries) return
    benchmarkSeries.applyOptions({
      title: value || '沪深300'
    })
  }
)
</script>

<template>
  <div ref="chartRef" class="w-full h-full min-h-[300px]"></div>
</template>
