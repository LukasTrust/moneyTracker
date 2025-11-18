import React from 'react'
import '@testing-library/jest-dom'
import { render } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFetchAccounts = vi.fn()

vi.mock('../../store', () => ({
  useAccountStore: () => ({
    accounts: [],
    fetchAccounts: mockFetchAccounts,
  })
}))

import { useAccounts } from '../../hooks/useAccounts'

function TestComp() {
  const store = useAccounts()
  return <div data-count={store.accounts.length} />
}

describe('useAccounts hook', () => {
  beforeEach(() => {
  vi.clearAllMocks()
  })

  it('calls fetchAccounts on mount when accounts empty', () => {
    render(<TestComp />)
    expect(mockFetchAccounts).toHaveBeenCalled()
  })
})
