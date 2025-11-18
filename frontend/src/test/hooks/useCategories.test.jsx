import React from 'react'
import '@testing-library/jest-dom'
import { render } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFetchCategories = vi.fn()
const mockFetchMappings = vi.fn()
const mockUpdateMapping = vi.fn()
const mockBulkUpdateMappings = vi.fn()

const mockCategoryStore = {
  categories: [],
  fetchCategories: mockFetchCategories,
  mappings: {},
  fetchMappings: mockFetchMappings,
  updateMapping: mockUpdateMapping,
  bulkUpdateMappings: mockBulkUpdateMappings,
}

vi.mock('../../store', () => ({
  useCategoryStore: () => mockCategoryStore,
}))

import { useCategories, useCategoryMappings } from '../../hooks/useCategories'

function TestComp() {
  useCategories(true)
  return <div />
}

function MappingsComp({ accountId }) {
  const res = useCategoryMappings(accountId)
  return <div data-mapping={JSON.stringify(res.mappings || {})} />
}

describe('useCategories hook', () => {
  beforeEach(() => {
  vi.clearAllMocks()
  })

  it('calls fetchCategories on mount when autoFetch true', () => {
    render(<TestComp />)
    expect(mockFetchCategories).toHaveBeenCalled()
  })

  it('useCategoryMappings exposes mapping helpers via component', () => {
    // set mappings on shared mock store
    mockCategoryStore.mappings = { 5: { a: 1 } }

    const { container } = render(<MappingsComp accountId={5} />)
    const el = container.querySelector('[data-mapping]')
    expect(el).toBeTruthy()
    expect(JSON.parse(el.getAttribute('data-mapping'))).toEqual({ a: 1 })
  })
})
