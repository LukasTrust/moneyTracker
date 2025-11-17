import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

vi.mock('../../services/api', () => ({
  default: {
    get: (...args) => mockGet(...args),
    post: (...args) => mockPost(...args),
    put: (...args) => mockPut(...args),
    delete: (...args) => mockDelete(...args),
  }
}))

import transferService, { getAllTransfers, getTransfer, createTransfer, updateTransfer, deleteTransfer, detectTransfers, getTransferStats, getTransferForTransaction, bulkDetectAndCreate } from '../../services/transferService'

beforeEach(() => {
  vi.resetAllMocks()
})

describe('transferService', () => {
  it('getAllTransfers calls api.get and returns data', async () => {
    mockGet.mockResolvedValue({ data: [{ id: 1 }] })
    const res = await getAllTransfers({ account_id: 5 })
    expect(mockGet).toHaveBeenCalledWith('/transfers', { params: { account_id: 5 } })
    expect(res).toEqual([{ id: 1 }])
  })

  it('create/update/delete use correct endpoints', async () => {
    mockPost.mockResolvedValue({ data: { id: 2 } })
    const created = await createTransfer({ from_transaction_id: 1, to_transaction_id: 2 })
    expect(mockPost).toHaveBeenCalledWith('/transfers', { from_transaction_id: 1, to_transaction_id: 2 })
    expect(created).toEqual({ id: 2 })

    mockPut.mockResolvedValue({ data: { id: 2, notes: 'ok' } })
    const updated = await updateTransfer(2, { notes: 'ok' })
    expect(mockPut).toHaveBeenCalledWith('/transfers/2', { notes: 'ok' })
    expect(updated).toEqual({ id: 2, notes: 'ok' })

    mockDelete.mockResolvedValue({ data: { success: true } })
    const deleted = await deleteTransfer(2)
    expect(mockDelete).toHaveBeenCalledWith('/transfers/2')
    expect(deleted).toEqual({ success: true })
  })

  it('detectTransfers and bulkDetectAndCreate post to detect', async () => {
    mockPost.mockResolvedValue({ data: { candidates: [] } })
    const det = await detectTransfers({ min_confidence: 0.7 })
    expect(mockPost).toHaveBeenCalledWith('/transfers/detect', { min_confidence: 0.7 })
    expect(det).toEqual({ candidates: [] })

    mockPost.mockResolvedValue({ data: { created: 1 } })
    const bulk = await bulkDetectAndCreate({ auto_create: true })
    expect(mockPost).toHaveBeenCalledWith('/transfers/detect', { auto_create: true })
    expect(bulk).toEqual({ created: 1 })
  })

  it('getTransfer/getTransferForTransaction/getTransferStats use correct endpoints', async () => {
    mockGet.mockResolvedValue({ data: { id: 3 } })
    const t = await getTransfer(3)
    expect(mockGet).toHaveBeenCalledWith('/transfers/3')
    expect(t).toEqual({ id: 3 })

    mockGet.mockResolvedValue({ data: { transfer_id: 4 } })
    const tf = await getTransferForTransaction(10)
    expect(mockGet).toHaveBeenCalledWith('/transactions/10/transfer')
    expect(tf).toEqual({ transfer_id: 4 })

    mockGet.mockResolvedValue({ data: { total_transfers: 2 } })
    const stats = await getTransferStats(7)
    expect(mockGet).toHaveBeenCalledWith('/transfers/stats', { params: { account_id: 7 } })
    expect(stats).toEqual({ total_transfers: 2 })
  })
})
