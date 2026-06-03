import { describe, it, expect } from 'vitest'

describe('基础工具函数', () => {
  it('1 + 1 = 2', () => {
    expect(1 + 1).toBe(2)
  })

  it('字符串去除空白', () => {
    expect('  hello  '.trim()).toBe('hello')
  })

  it('数组 filter 正确', () => {
    expect([1, 2, 3, 4].filter(x => x > 2)).toEqual([3, 4])
  })
})
