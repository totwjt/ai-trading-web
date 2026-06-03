import { describe, it, expect } from 'vitest'

function normalizeSimulation(item: any) {
  return {
    ...item,
    strategyName: item.strategyName || item.strategy_name || '',
    statusText: item.statusText || item.status_text || '',
    initialCapital: item.initialCapital ?? item.initial_capital ?? 0,
    currentCapital: item.currentCapital ?? item.current_capital ?? 0,
    totalReturn: item.totalReturn ?? item.total_return ?? 0,
    todayReturn: item.todayReturn ?? item.today_return ?? 0,
    todayPL: item.todayPL ?? item.today_pl ?? 0,
    holdingsValue: item.holdingsValue ?? item.holdings_value ?? 0,
    holdingsCount: item.holdingsCount ?? item.holdings_count ?? 0,
    winRate: item.winRate ?? item.win_rate ?? 0,
    tradeCount: item.tradeCount ?? item.trade_count ?? 0,
    startDate: item.startDate || item.start_date || '',
    lastTradeTime: item.lastTradeTime || item.last_trade_time || item.lastTradeDateTime || '',
    availableCapital: item.availableCapital ?? item.available_capital ?? 0,
    frozenCapital: item.frozenCapital ?? item.frozen_capital ?? 0,
  }
}

describe('normalizeSimulation', () => {
  it('camelCase input', () => {
    const input = {
      id: 1, name: 'test', strategyName: '均线策略', statusText: '运行中',
      initialCapital: 1000000, totalReturn: 12.5,
    }
    const result = normalizeSimulation(input)
    expect(result.strategyName).toBe('均线策略')
    expect(result.initialCapital).toBe(1000000)
    expect(result.totalReturn).toBe(12.5)
  })

  it('snake_case input', () => {
    const input = {
      id: 2, name: 'test2', strategy_name: '布林线策略', status_text: '已暂停',
      initial_capital: 500000, total_return: 8.3,
      start_date: '2024-01-01', last_trade_time: '2024-06-01 10:30:00',
    }
    const result = normalizeSimulation(input)
    expect(result.strategyName).toBe('布林线策略')
    expect(result.statusText).toBe('已暂停')
    expect(result.initialCapital).toBe(500000)
    expect(result.totalReturn).toBe(8.3)
    expect(result.startDate).toBe('2024-01-01')
    expect(result.lastTradeTime).toBe('2024-06-01 10:30:00')
  })

  it('优先使用 camelCase', () => {
    const input = { strategyName: 'camel', strategy_name: 'snake', initialCapital: 100, initial_capital: 200 }
    const result = normalizeSimulation(input)
    expect(result.strategyName).toBe('camel')
    expect(result.initialCapital).toBe(100)
  })

  it('null/undefined 为默认值', () => {
    const result = normalizeSimulation({})
    expect(result.strategyName).toBe('')
    expect(result.initialCapital).toBe(0)
    expect(result.startDate).toBe('')
  })

  it('保留额外字段', () => {
    const result = normalizeSimulation({ id: 1, extra_field: 'extra' })
    expect(result.id).toBe(1)
    expect(result.extra_field).toBe('extra')
  })

  it('lastTradeDateTime 兼容', () => {
    const result = normalizeSimulation({ lastTradeDateTime: '2024-05-01 09:00:00' })
    expect(result.lastTradeTime).toBe('2024-05-01 09:00:00')
  })

  it('todayPL 来自 today_pl', () => {
    const result = normalizeSimulation({ today_pl: -1500 })
    expect(result.todayPL).toBe(-1500)
  })
})

function normalizeHolding(item: any) {
  return {
    ...item,
    code: item.code || item.symbol || item.ts_code || '',
    avgCost: item.avgCost ?? item.avg_cost ?? item.cost_price ?? 0,
    currentPrice: item.currentPrice ?? item.current_price ?? 0,
    marketValue: item.marketValue ?? item.market_value ?? 0,
    pl: item.pl ?? item.profit_loss ?? 0,
    plPercent: item.plPercent ?? item.pl_percent ?? item.profit_loss_percent ?? 0,
  }
}

describe('normalizeHolding', () => {
  it('camelCase input', () => {
    const input = { name: '茅台', code: '600519', avgCost: 150, currentPrice: 180, marketValue: 180000, pl: 30000, plPercent: 20 }
    const result = normalizeHolding(input)
    expect(result.code).toBe('600519')
    expect(result.avgCost).toBe(150)
    expect(result.pl).toBe(30000)
  })

  it('snake_case input', () => {
    const input = { name: '茅台', ts_code: '600519.SH', cost_price: 150, profit_loss: 30000, profit_loss_percent: 20 }
    const result = normalizeHolding(input)
    expect(result.code).toBe('600519.SH')
    expect(result.avgCost).toBe(150)
    expect(result.pl).toBe(30000)
    expect(result.plPercent).toBe(20)
  })

  it('优先使用 camelCase', () => {
    const result = normalizeHolding({ avgCost: 100, avg_cost: 200, code: '000001', symbol: '000002' })
    expect(result.avgCost).toBe(100)
    expect(result.code).toBe('000001')
  })

  it('空输入', () => {
    const result = normalizeHolding({})
    expect(result.code).toBe('')
    expect(result.avgCost).toBe(0)
  })

  it('symbol fallback', () => {
    const result = normalizeHolding({ symbol: '300750' })
    expect(result.code).toBe('300750')
  })
})

function normalizeTrade(item: any) {
  return {
    ...item,
    time: item.time || item.timestamp || '',
    stockName: item.stockName || item.stock_name || item.name || '',
    stockCode: item.stockCode || item.stock_code || item.symbol || '',
    direction: item.direction || item.trade_type || '',
    directionText: item.directionText || item.direction_text || '',
    amount: item.amount ?? ((item.price * item.quantity) || 0),
    status: item.status || 'completed',
  }
}

describe('normalizeTrade', () => {
  it('camelCase input', () => {
    const input = { id: 1, time: '10:30:00', stockName: '茅台', stockCode: '600519', direction: 'buy', price: 150, quantity: 100, amount: 15000 }
    const result = normalizeTrade(input)
    expect(result.time).toBe('10:30:00')
    expect(result.stockName).toBe('茅台')
    expect(result.stockCode).toBe('600519')
    expect(result.direction).toBe('buy')
  })

  it('snake_case input', () => {
    const input = { timestamp: '10:30:00', name: '茅台', symbol: '600519', trade_type: 'buy', price: 150, quantity: 100 }
    const result = normalizeTrade(input)
    expect(result.time).toBe('10:30:00')
    expect(result.stockName).toBe('茅台')
    expect(result.stockCode).toBe('600519')
    expect(result.direction).toBe('buy')
    expect(result.amount).toBe(15000)
  })

  it('优先使用 camelCase', () => {
    const result = normalizeTrade({ time: 'camel', timestamp: 'snake' })
    expect(result.time).toBe('camel')
  })

  it('amount 未提供时自动计算', () => {
    const result = normalizeTrade({ price: 100, quantity: 200 })
    expect(result.amount).toBe(20000)
  })

  it('amount 已提供时不做计算', () => {
    const result = normalizeTrade({ price: 100, quantity: 200, amount: 999 })
    expect(result.amount).toBe(999)
  })

  it('默认 status', () => {
    expect(normalizeTrade({}).status).toBe('completed')
  })

  it('空输入', () => {
    const result = normalizeTrade({})
    expect(result.time).toBe('')
    expect(result.stockName).toBe('')
    expect(result.stockCode).toBe('')
    expect(result.direction).toBe('')
    expect(result.amount).toBe(0)
  })

  it('directionText', () => {
    const result = normalizeTrade({ direction: 'buy', direction_text: '买入' })
    expect(result.directionText).toBe('买入')
  })
})
