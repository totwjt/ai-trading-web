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
      textColor: '#94A3B8'
    },
    grid: {
      vertLines: { color: '#F1F5F9' },
      horzLines: { color: '#F1F5F9' }
    },
    rightPriceScale: {
      borderColor: '#E2E8F0'
    },
    timeScale: {
      borderColor: '#E2E8F0',
      timeVisible: true,
      secondsVisible: false
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
    }
  })

  equitySeries = chart.addLineSeries({
    color: '#0066FF',
    lineWidth: 2,
    title: '策略'
  })

  benchmarkSeries = chart.addLineSeries({
    color: '#CBD5E1',
    lineWidth: 2,
    lineStyle: LineStyle.Dashed,
    title: props.benchmark || '沪深300'
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
