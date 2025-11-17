import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mocks
const mockRefetch = vi.fn()
const mockDeleteCategory = vi.fn(() => Promise.resolve())
const mockShowToast = vi.fn()

const useCategoryDataMockImpl = vi.fn(() => ({
  categories: [],
  loading: false,
  error: null,
  refetch: mockRefetch,
}))

vi.mock('../../../hooks/useDataFetch', () => ({
  useCategoryData: (...args) => useCategoryDataMockImpl(...args),
}))

vi.mock('../../../services/categoryService', () => ({
  default: {
    deleteCategory: (...args) => mockDeleteCategory(...args),
  }
}))

vi.mock('../../../hooks/useToast', () => ({
  useToast: () => ({ showToast: mockShowToast }),
}))

describe('CategoryManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useCategoryDataMockImpl.mockImplementation(() => ({
      categories: [],
      loading: false,
      error: null,
      refetch: mockRefetch,
    }))
  })

  it('opens confirm modal and deletes category on confirm', async () => {
    // Provide one category
    useCategoryDataMockImpl.mockImplementation(() => ({
      categories: [{ id: 5, name: 'TestCat', color: '#ff0000', icon: '💰' }],
      loading: false,
      error: null,
      refetch: mockRefetch,
    }))

    const { default: Component } = await import('../../../components/categories/CategoryManager')
    render(<Component />)

    // Find the delete button for the category (title="Löschen")
    const deleteBtn = await screen.findByTitle('Löschen')
    fireEvent.click(deleteBtn)

    // Modal should open
    const dialog = await screen.findByRole('dialog')
    const { within } = await import('@testing-library/react')
    expect(within(dialog).getByText(/TestCat/)).toBeInTheDocument()

    // Click Löschen in modal
    const confirmBtn = within(dialog).getByText('Löschen')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockDeleteCategory).toHaveBeenCalledWith(5)
      expect(mockShowToast).toHaveBeenCalledWith('Kategorie gelöscht', 'success')
    })
  })

  it('shows error toast when delete fails', async () => {
    // Provide one category
    useCategoryDataMockImpl.mockImplementation(() => ({
      categories: [{ id: 6, name: 'ErrCat', color: '#00ff00', icon: '🧾' }],
      loading: false,
      error: null,
      refetch: mockRefetch,
    }))

    mockDeleteCategory.mockRejectedValueOnce(new Error('boom'))

    const { default: Component } = await import('../../../components/categories/CategoryManager')
    render(<Component />)

    const deleteBtn = await screen.findByTitle('Löschen')
    fireEvent.click(deleteBtn)

    const dialog = await screen.findByRole('dialog')
    const { within } = await import('@testing-library/react')
    const confirmBtn = within(dialog).getByText('Löschen')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockDeleteCategory).toHaveBeenCalledWith(6)
      expect(mockShowToast).toHaveBeenCalledWith('Fehler beim Löschen der Kategorie', 'error')
    })
  })
})
