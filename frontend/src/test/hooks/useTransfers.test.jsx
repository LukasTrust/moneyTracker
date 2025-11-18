import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const sampleTransfers = [{ id: 1, amount: 50 }]

vi.mock('../../services/transferService', () => ({
  getAllTransfers: (params) => Promise.resolve(sampleTransfers),
  getTransferForTransaction: (id) => Promise.resolve({ id, transfer_id: 10 }),
  detectTransfers: () => Promise.resolve({ candidates: [] }),
  createTransfer: () => Promise.resolve({ success: true }),
  deleteTransfer: () => Promise.resolve(),
  getTransferStats: () => Promise.resolve({ total_transfers: 1 }),
}))

import { useTransfers, useTransferForTransaction, useTransferDetection, useTransferStats } from '../../hooks/useTransfers'

function UseTransfersComp() {
  const { transfers, loading } = useTransfers()
  return <div data-count={transfers.length} data-loading={loading ? '1' : '0'} />
}

function UseTransferForTxComp({ transactionId }) {
  const { transfer, loading } = useTransferForTransaction(transactionId)
  return <div data-id={transfer?.transfer_id || ''} data-loading={loading ? '1' : '0'} />
}

function DetectionComp() {
  const hook = useTransferDetection()
  return (
    <div>
      <button onClick={() => hook.detect()}>detect</button>
      <div data-candidates-count={hook.candidates.length} />
    </div>
  )
}

function StatsComp() {
  const hook = useTransferStats()
  return (
    <div>
      <button onClick={() => hook.refetch()}>refetch</button>
      <div data-stats={JSON.stringify(hook.stats || {})} />
    </div>
  )
}

describe('useTransfers hooks', () => {
  beforeEach(() => vi.clearAllMocks())

  it('useTransfers loads transfers on mount', async () => {
    const { container } = render(<UseTransfersComp />)
    await waitFor(() => expect(container.querySelector('[data-count]')).toBeTruthy())
    expect(container.querySelector('[data-count]').getAttribute('data-count')).toBe('1')
  })

  it('useTransferForTransaction fetches transfer', async () => {
    const { container } = render(<UseTransferForTxComp transactionId={5} />)
    await waitFor(() => expect(container.querySelector('[data-id]')).toBeTruthy())
    expect(container.querySelector('[data-id]').getAttribute('data-id')).toBe('10')
  })

  it('useTransferDetection exposes detect and candidates via component', async () => {
    const { container } = render(<DetectionComp />)
    const btn = container.querySelector('button')
    btn && btn.click()
    await waitFor(() => expect(container.querySelector('[data-candidates-count]')).toBeTruthy())
    expect(container.querySelector('[data-candidates-count]').getAttribute('data-candidates-count')).toBe('0')
  })

  it('useTransferStats returns stats via component', async () => {
    const { container } = render(<StatsComp />)
    const btn = container.querySelector('button')
    btn && btn.click()
    await waitFor(() => expect(container.querySelector('[data-stats]')).toBeTruthy())
    expect(JSON.parse(container.querySelector('[data-stats]').getAttribute('data-stats'))).toHaveProperty('total_transfers', 1)
  })
})
