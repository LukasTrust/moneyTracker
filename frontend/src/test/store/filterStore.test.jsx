import { describe, it, expect, beforeEach } from 'vitest'
import { useFilterStore, DATE_PRESETS, TRANSACTION_TYPES } from '../../store/filterStore'

describe('filterStore', () => {
  beforeEach(() => {
    // reset to defaults using provided resetFilters helper
    useFilterStore.getState().resetFilters()
  })

  it('applyDatePreset ALL sets null dates', () => {
    useFilterStore.getState().applyDatePreset('ALL')
    const s = useFilterStore.getState()
    expect(s.datePreset).toBe('ALL')
    expect(s.fromDate).toBeNull()
    expect(s.toDate).toBeNull()
  })

  it('setAccountFilter and toggleAccount work', () => {
    useFilterStore.getState().setAccountFilter([1])
    expect(useFilterStore.getState().selectedAccountIds).toEqual([1])

    useFilterStore.getState().toggleAccount(2)
    expect(useFilterStore.getState().selectedAccountIds).toContain(2)

    useFilterStore.getState().toggleAccount(2)
    expect(useFilterStore.getState().selectedAccountIds).not.toContain(2)
  })

  it('setCategoryFilter and toggleCategory work', () => {
    useFilterStore.getState().setCategoryFilter(5)
    expect(useFilterStore.getState().selectedCategoryIds).toEqual([5])

    useFilterStore.getState().toggleCategory(6)
    expect(useFilterStore.getState().selectedCategoryIds).toContain(6)
  })

  it('setAmountRange and getQueryParams include amounts', () => {
    useFilterStore.getState().setAmountRange(10, 50)
    const params = useFilterStore.getState().getQueryParams()
    expect(params.minAmount).toBe(10)
    expect(params.maxAmount).toBe(50)
  })

  it('setSearchQuery and hasActiveFilters work and getActiveFilterCount increments', () => {
    useFilterStore.getState().resetFilters()
    expect(useFilterStore.getState().hasActiveFilters()).toBe(false)

    useFilterStore.getState().setSearchQuery('abc')
    expect(useFilterStore.getState().hasActiveFilters()).toBe(true)
    expect(useFilterStore.getState().getActiveFilterCount()).toBeGreaterThan(0)
  })

  it('toggleFilters and resetFilters behave', () => {
    const before = useFilterStore.getState().showFilters
    useFilterStore.getState().toggleFilters()
    expect(useFilterStore.getState().showFilters).toBe(!before)

    useFilterStore.getState().resetFilters()
    expect(useFilterStore.getState().searchQuery).toBe('')
  })
})
