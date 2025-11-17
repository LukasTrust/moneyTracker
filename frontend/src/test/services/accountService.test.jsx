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

import accountService from '../../services/accountService'

beforeEach(() => vi.resetAllMocks())

describe('accountService', () => {
  it('getAccounts/getAccount/create/update/delete call api', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1 }] })
    const accounts = await accountService.getAccounts()
    expect(mockGet).toHaveBeenCalledWith('/accounts')
    expect(accounts).toEqual([{ id: 1 }])

    mockGet.mockResolvedValueOnce({ data: { id: 2 } })
    const acc = await accountService.getAccount(2)
    expect(mockGet).toHaveBeenCalledWith('/accounts/2')
    expect(acc).toEqual({ id: 2 })

    mockPost.mockResolvedValueOnce({ data: { id: 3 } })
    const created = await accountService.createAccount({ name: 'Foo' })
    expect(mockPost).toHaveBeenCalledWith('/accounts', { name: 'Foo' })
    expect(created).toEqual({ id: 3 })

    mockPut.mockResolvedValueOnce({ data: { id: 3, name: 'Bar' } })
    const updated = await accountService.updateAccount(3, { name: 'Bar' })
    expect(mockPut).toHaveBeenCalledWith('/accounts/3', { name: 'Bar' })
    expect(updated).toEqual({ id: 3, name: 'Bar' })

    mockDelete.mockResolvedValueOnce({ data: { success: true } })
    const deleted = await accountService.deleteAccount(3)
    expect(mockDelete).toHaveBeenCalledWith('/accounts/3')
    expect(deleted).toEqual({ success: true })
  })
})
