import { describe, it, expect, beforeEach, vi } from 'vitest'
import useBudgetStore from '../../store/budgetStore'

const mockGetBudgets = vi.fn()
const mockGetBudgetsWithProgress = vi.fn()
const mockGetBudgetSummary = vi.fn()
const mockGetBudget = vi.fn()
const mockCreateBudget = vi.fn()
const mockUpdateBudget = vi.fn()
const mockDeleteBudget = vi.fn()

vi.mock('../../services/budgetService', () => ({
  default: {
    getBudgets: (...args) => mockGetBudgets(...args),
    getBudgetsWithProgress: (...args) => mockGetBudgetsWithProgress(...args),
    getBudgetSummary: (...args) => mockGetBudgetSummary(...args),
    getBudget: (...args) => mockGetBudget(...args),
    createBudget: (...args) => mockCreateBudget(...args),
    updateBudget: (...args) => mockUpdateBudget(...args),
    deleteBudget: (...args) => mockDeleteBudget(...args),
  }
}))

describe('budgetStore', () => {
  beforeEach(() => {
    useBudgetStore.setState({ budgets: [], budgetsWithProgress: [], summary: null, loading: false, error: null, lastFetch: null })
    vi.resetAllMocks()
  })

  it('fetchBudgets sets budgets', async () => {
    mockGetBudgets.mockResolvedValueOnce([{ id: 1 }])
    await useBudgetStore.getState().fetchBudgets({ force: true })
    expect(useBudgetStore.getState().budgets).toEqual([{ id: 1 }])
  })

  it('createBudget adds new budget', async () => {
    mockCreateBudget.mockResolvedValueOnce({ id: 2 })
    const res = await useBudgetStore.getState().createBudget({ amount: 10 })
    expect(res).toEqual({ id: 2 })
    expect(useBudgetStore.getState().budgets).toContainEqual({ id: 2 })
  })

  it('createMonthlyBudget delegates to createBudget', async () => {
    mockCreateBudget.mockResolvedValueOnce({ id: 3 })
    const res = await useBudgetStore.getState().createMonthlyBudget(5, 100)
    expect(res).toEqual({ id: 3 })
    expect(useBudgetStore.getState().budgets).toContainEqual({ id: 3 })
  })

  it('invalidateCache sets lastFetch null', () => {
    useBudgetStore.setState({ lastFetch: Date.now() })
    useBudgetStore.getState().invalidateCache()
    expect(useBudgetStore.getState().lastFetch).toBeNull()
  })
})
