import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockDelete = vi.fn()

vi.mock('../../services/api', () => ({
  default: {
    get: (...args) => mockGet(...args),
    post: (...args) => mockPost(...args),
    delete: (...args) => mockDelete(...args),
  }
}))

import insightsService from '../../services/insightsService'

beforeEach(() => vi.resetAllMocks())

describe('insightsService', () => {
  it('getSeverityColors and getInsightTypeLabel pure helpers', () => {
    const info = insightsService.getSeverityColors('info')
    expect(info).toHaveProperty('bg', 'bg-blue-50')

    const label = insightsService.getInsightTypeLabel('mom_increase')
    expect(label).toContain('Ausgaben')
  })

  it('API functions call correct endpoints', async () => {
    mockGet.mockResolvedValueOnce({ data: { insights: [] } })
    const res = await insightsService.getInsights({ accountId: 1 })
    expect(mockGet).toHaveBeenCalled()
    expect(res).toEqual({ insights: [] })

    mockPost.mockResolvedValueOnce({ data: { success: true } })
    const gen = await insightsService.generateInsights({ accountId: 1 })
    expect(mockPost).toHaveBeenCalledWith('/insights/generate', { account_id: 1, generation_types: null, force_regenerate: false })
    expect(gen).toEqual({ success: true })

    mockPost.mockResolvedValueOnce({ data: { success: true } })
    const dismiss = await insightsService.dismissInsight(5)
    expect(mockPost).toHaveBeenCalledWith('/insights/dismiss/5')
    expect(dismiss).toEqual({ success: true })

    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    const deleted = await insightsService.deleteInsight(6)
    expect(mockDelete).toHaveBeenCalledWith('/insights/6')
    expect(deleted).toEqual({ success: true })
  })
})
