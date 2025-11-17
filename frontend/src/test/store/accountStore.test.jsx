import { describe, it, expect, beforeEach, vi } from 'vitest'
import useAccountStore from '../../store/accountStore'

const mockGetAccounts = vi.fn()
const mockGetAccount = vi.fn()
const mockCreateAccount = vi.fn()
const mockUpdateAccount = vi.fn()
const mockDeleteAccount = vi.fn()

vi.mock('../../services/accountService', () => ({
  default: {
    getAccounts: (...args) => mockGetAccounts(...args),
    getAccount: (...args) => mockGetAccount(...args),
    createAccount: (...args) => mockCreateAccount(...args),
    updateAccount: (...args) => mockUpdateAccount(...args),
    deleteAccount: (...args) => mockDeleteAccount(...args),
  }
}))

describe('accountStore', () => {
  beforeEach(() => {
    useAccountStore.setState({ accounts: [], currentAccount: null, loading: false, error: null })
    vi.resetAllMocks()
  })

  it('fetchAccounts loads accounts', async () => {
    mockGetAccounts.mockResolvedValueOnce([{ id: 1 }])
    await useAccountStore.getState().fetchAccounts()
    expect(useAccountStore.getState().accounts).toEqual([{ id: 1 }])
  })

  it('fetchAccount sets currentAccount', async () => {
    mockGetAccount.mockResolvedValueOnce({ id: 2 })
    await useAccountStore.getState().fetchAccount(2)
    expect(useAccountStore.getState().currentAccount).toEqual({ id: 2 })
  })

  it('createAccount appends and returns created account', async () => {
    mockCreateAccount.mockResolvedValueOnce({ id: 3 })
    const created = await useAccountStore.getState().createAccount({ name: 'X' })
    expect(created).toEqual({ id: 3 })
    expect(useAccountStore.getState().accounts).toContainEqual({ id: 3 })
  })

  it('updateAccount optimistic updates immediately', async () => {
    // prepare state
    useAccountStore.setState({ accounts: [{ id: 4, name: 'Old' }], currentAccount: { id: 4, name: 'Old' } })

    mockUpdateAccount.mockResolvedValueOnce({ account: { id: 4, name: 'New' } })

    const p = useAccountStore.getState().updateAccount(4, { name: 'New' }, true)
    // optimistic applied synchronously
    expect(useAccountStore.getState().accounts[0].name).toBe('New')
    const res = await p
    expect(res).toEqual({ id: 4, name: 'New' })
  })

  it('deleteAccount removes account', async () => {
    useAccountStore.setState({ accounts: [{ id: 5 }], currentAccount: { id: 5 } })
    mockDeleteAccount.mockResolvedValueOnce({})
    await useAccountStore.getState().deleteAccount(5)
    expect(useAccountStore.getState().accounts.find(a => a.id === 5)).toBeUndefined()
    expect(useAccountStore.getState().currentAccount).toBeNull()
  })
})
