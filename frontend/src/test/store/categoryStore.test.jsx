import { describe, it, expect, beforeEach, vi } from 'vitest'
import useCategoryStore from '../../store/categoryStore'

const mockGetCategories = vi.fn()
const mockGetMappings = vi.fn()
const mockUpdateMapping = vi.fn()
const mockBulkUpdateMappings = vi.fn()

vi.mock('../../services/categoryService', () => ({
  default: {
    getCategories: (...args) => mockGetCategories(...args),
    getMappings: (...args) => mockGetMappings(...args),
    updateMapping: (...args) => mockUpdateMapping(...args),
    bulkUpdateMappings: (...args) => mockBulkUpdateMappings(...args),
  }
}))

describe('categoryStore', () => {
  beforeEach(() => {
    useCategoryStore.setState({ categories: [], mappings: {}, loading: false, error: null, lastFetch: null })
    vi.resetAllMocks()
  })

  it('fetchCategories sets categories', async () => {
    mockGetCategories.mockResolvedValueOnce([{ id: 1, name: 'Food' }])
    await useCategoryStore.getState().fetchCategories(true)
    expect(useCategoryStore.getState().categories).toEqual([{ id: 1, name: 'Food' }])
  })

  it('fetchMappings stores mapping under account id', async () => {
    mockGetMappings.mockResolvedValueOnce({ mappings: { A: 1 } })
    await useCategoryStore.getState().fetchMappings(9)
    expect(useCategoryStore.getState().mappings[9]).toEqual({ A: 1 })
  })

  it('updateMapping updates mapping in state', async () => {
    mockUpdateMapping.mockResolvedValueOnce({})
    useCategoryStore.setState({ mappings: { 7: { Old: 2 } } })
    await useCategoryStore.getState().updateMapping(7, 'New', 5)
    expect(useCategoryStore.getState().mappings[7]['New']).toBe(5)
  })

  it('getMappingForRecipient returns null when missing and helpers work', () => {
    useCategoryStore.setState({ categories: [{ id: 11, name: 'X' }], mappings: { 3: { Rec: 11 } } })
    expect(useCategoryStore.getState().getCategoryById(11).name).toBe('X')
    expect(useCategoryStore.getState().getMappingForRecipient(3, 'Rec')).toBe(11)
  })
})
