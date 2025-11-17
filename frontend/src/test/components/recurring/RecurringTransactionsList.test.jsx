import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
// We'll import the component dynamically in tests after setting up mocks
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the useRecurring hook with a mutable implementation so tests can change returned data
const mockRefresh = vi.fn()
const mockRemove = vi.fn(() => Promise.resolve())
const mockTrigger = vi.fn(() => Promise.resolve({ created: 0, updated: 0, deleted: 0 }))

const useRecurringMockImpl = vi.fn(() => ({
  recurring: [],
  stats: null,
  loading: false,
  error: null,
  triggerDetection: mockTrigger,
  toggle: vi.fn(),
  remove: mockRemove,
  refresh: mockRefresh,
}))

vi.mock('../../../hooks/useRecurring', () => ({
  useRecurring: (...args) => useRecurringMockImpl(...args),
}))

// Mock the useToast hook
const mockShowToast = vi.fn()
vi.mock('../../../hooks/useToast', () => ({
  useToast: () => ({ showToast: mockShowToast }),
}))

describe('RecurringTransactionsList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // reset the default impl
    useRecurringMockImpl.mockImplementation(() => ({
      recurring: [],
      stats: null,
      loading: false,
      error: null,
      triggerDetection: mockTrigger,
      toggle: vi.fn(),
      remove: mockRemove,
      refresh: mockRefresh,
    }))
  })

  it('calls refresh when includeInactive checkbox is toggled', async () => {
    const { default: RecurringTransactionsList } = await import('../../../components/recurring/RecurringTransactionsList')
    render(<RecurringTransactionsList />)

    const checkbox = screen.getByLabelText(/inaktive verträge anzeigen/i)
    // toggle it on
    fireEvent.click(checkbox)

    expect(mockRefresh).toHaveBeenCalledWith(true)

    // toggle it off
    fireEvent.click(checkbox)
    expect(mockRefresh).toHaveBeenCalledWith(false)
  })

  it('opens confirm modal and deletes on confirm, then shows toast', async () => {
    // Provide a specific implementation for this test: one recurring item
    useRecurringMockImpl.mockImplementation(() => ({
      recurring: [
        {
          id: 1,
          recipient: 'ACME GmbH',
          is_active: true,
          occurrence_count: 3,
          confidence_score: 1.0,
          average_amount: 12.34,
          average_interval_days: 30,
          monthly_cost: 12.34,
          last_occurrence: '2023-09-01',
          next_expected_date: '2023-10-01',
        },
      ],
      stats: null,
      loading: false,
      error: null,
      triggerDetection: mockTrigger,
      toggle: vi.fn(),
      remove: mockRemove,
      refresh: mockRefresh,
    }))

    // Import the component after mocking to ensure it picks up the mocked hook
    const { default: Component } = await import('../../../components/recurring/RecurringTransactionsList')
    render(<Component />)

    // Find the delete button (title attribute 'Löschen')
    const deleteBtn = screen.getByTitle('Löschen')
    fireEvent.click(deleteBtn)

    // Modal should be open
    const dialog = await screen.findByRole('dialog')
    // Confirm the recipient is shown inside the modal
    const { within } = await import('@testing-library/react')
    expect(within(dialog).getByText(/ACME GmbH/)).toBeInTheDocument()

    // Click the Löschen button inside modal
    const confirmBtn = within(dialog).getByText('Löschen')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockRemove).toHaveBeenCalledWith(1)
      expect(mockShowToast).toHaveBeenCalledWith('Vertrag gelöscht', 'success')
    })
  })

  it('calls triggerDetection when detection button is clicked and shows toast', async () => {
    // Provide default empty data but ensure triggerDetection is mocked
    useRecurringMockImpl.mockImplementation(() => ({
      recurring: [],
      stats: null,
      loading: false,
      error: null,
      triggerDetection: mockTrigger,
      toggle: vi.fn(),
      remove: mockRemove,
      refresh: mockRefresh,
    }))

    const { default: RecurringTransactionsList } = await import('../../../components/recurring/RecurringTransactionsList')
    render(<RecurringTransactionsList />)

  const detectBtn = screen.getByRole('button', { name: /Erkennung starten/i })
    fireEvent.click(detectBtn)

    await waitFor(() => {
      expect(mockTrigger).toHaveBeenCalled()
      expect(mockShowToast).toHaveBeenCalled()
      // The toast message contains 'Erkennung abgeschlossen' on success
      expect(mockShowToast.mock.calls[0][0]).toMatch(/Erkennung abgeschlossen/)
    })
  })

  it('shows error toast when detection fails', async () => {
    // Make triggerDetection reject
    mockTrigger.mockRejectedValueOnce(new Error('boom'))

    const { default: RecurringTransactionsList } = await import('../../../components/recurring/RecurringTransactionsList')
    render(<RecurringTransactionsList />)

    const detectBtn = screen.getByRole('button', { name: /Erkennung starten/i })
    fireEvent.click(detectBtn)

    await waitFor(() => {
      expect(mockTrigger).toHaveBeenCalled()
      // An error toast should be shown
      expect(mockShowToast).toHaveBeenCalledWith(expect.stringMatching(/Fehler bei der Erkennung/), 'error')
    })
  })

  it('shows error toast when delete fails', async () => {
    // Provide one recurring item
    useRecurringMockImpl.mockImplementation(() => ({
      recurring: [
        {
          id: 2,
          recipient: 'FailCorp',
          is_active: true,
          occurrence_count: 2,
          confidence_score: 0.8,
          average_amount: 5.0,
          average_interval_days: 30,
          monthly_cost: 5.0,
          last_occurrence: '2023-09-01',
          next_expected_date: '2023-10-01',
        },
      ],
      stats: null,
      loading: false,
      error: null,
      triggerDetection: mockTrigger,
      toggle: vi.fn(),
      remove: mockRemove,
      refresh: mockRefresh,
    }))

    // Make remove reject
    mockRemove.mockRejectedValueOnce(new Error('del-fail'))

    const { default: Component } = await import('../../../components/recurring/RecurringTransactionsList')
    render(<Component />)

    const deleteBtn = screen.getByTitle('Löschen')
    fireEvent.click(deleteBtn)

    const dialog = await screen.findByRole('dialog')
    const { within } = await import('@testing-library/react')
    const confirmBtn = within(dialog).getByText('Löschen')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockRemove).toHaveBeenCalledWith(2)
      expect(mockShowToast).toHaveBeenCalledWith(expect.stringMatching(/Fehler beim Löschen/), 'error')
    })
  })
})
