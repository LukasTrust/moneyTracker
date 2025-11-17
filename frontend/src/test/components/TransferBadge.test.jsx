import React from 'react'
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import TransferBadge, { TransferIndicator } from '../../components/common/TransferBadge'
import { describe, it, expect } from 'vitest'

describe('TransferBadge component', () => {
  it('returns null when no transfer provided', () => {
    const { container } = render(<TransferBadge transfer={null} currentTransactionId={1} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders outgoing transfer and details', () => {
    const transfer = {
      from_transaction_id: 1,
      to_transaction_id: 2,
      from_account_name: 'Checking',
      to_account_name: 'Savings',
      is_auto_detected: true,
      confidence_score: 0.85,
    }

    render(<TransferBadge transfer={transfer} currentTransactionId={1} showDetails={true} />)

    expect(screen.getByText('Transfer')).toBeInTheDocument()
    // showDetails should render linked account name
    expect(screen.getByText(/Savings/)).toBeInTheDocument()
  })

  it('TransferIndicator renders and shows icon', () => {
    const transfer = {
      from_transaction_id: 10,
    }
    const { container } = render(<TransferIndicator transfer={transfer} currentTransactionId={10} />)
    expect(container.textContent).toContain('🔄')
  })
})
