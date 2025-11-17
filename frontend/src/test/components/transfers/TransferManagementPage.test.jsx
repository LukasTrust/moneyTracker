import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetAllTransfers = vi.fn(() => Promise.resolve([
  { id: 11, amount: 50, from_account_name: 'A', to_account_name: 'B', transfer_date: '2023-10-01' }
]))
const mockDeleteTransfer = vi.fn(() => Promise.resolve())
const mockShowToast = vi.fn()

vi.mock('../../../services/transferService', () => ({
  getAllTransfers: (...args) => mockGetAllTransfers(...args),
  deleteTransfer: (...args) => mockDeleteTransfer(...args),
  detectTransfers: vi.fn(),
  createTransfer: vi.fn(),
}))

vi.mock('../../../hooks/useToast', () => ({
  useToast: () => ({ showToast: mockShowToast }),
}))

describe('TransferManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('opens unlink confirm modal and calls deleteTransfer on confirm', async () => {
    const { default: Component } = await import('../../../components/transfers/TransferManagementPage')
    render(<Component />)

    // Wait for the Unlink button to appear (transfer row)
    const unlinkBtn = await screen.findByTitle('Unlink transfer')
    fireEvent.click(unlinkBtn)

    // Modal should open
    const dialog = await screen.findByRole('dialog')
    const { within } = await import('@testing-library/react')
    expect(within(dialog).getByText(/Transfer wirklich entkoppeln/)).toBeInTheDocument()

    // Click Entkoppeln button
    const confirmBtn = within(dialog).getByText('Entkoppeln')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockDeleteTransfer).toHaveBeenCalledWith(11)
      expect(mockShowToast).toHaveBeenCalledWith('Transfer deleted successfully', 'success')
    })
  })

  it('shows error toast when deleteTransfer fails', async () => {
    // Make delete fail
    mockDeleteTransfer.mockRejectedValueOnce(new Error('boom'))

    const { default: Component } = await import('../../../components/transfers/TransferManagementPage')
    render(<Component />)

    const unlinkBtn = await screen.findByTitle('Unlink transfer')
    fireEvent.click(unlinkBtn)

    const dialog = await screen.findByRole('dialog')
    const { within } = await import('@testing-library/react')
    const confirmBtn = within(dialog).getByText('Entkoppeln')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockDeleteTransfer).toHaveBeenCalledWith(11)
      expect(mockShowToast).toHaveBeenCalledWith('Failed to delete transfer', 'error')
    })
  })
})
