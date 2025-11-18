import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockDelete = vi.fn()

vi.mock('../../services/api', () => ({
  default: {
    get: (...args) => mockGet(...args),
    post: (...args) => mockPost(...args),
    delete: (...args) => mockDelete(...args),
  }
}))

import mappingService from '../../services/mappingService'

beforeEach(() => vi.clearAllMocks())

describe('mappingService', () => {
  it('getMappings/saveMappings/deleteMappings call api correctly', async () => {
    mockGet.mockResolvedValueOnce({ data: { a: 1 } })
    const g = await mappingService.getMappings(5)
    expect(mockGet).toHaveBeenCalledWith('/accounts/5/mappings')
    expect(g).toEqual({ a: 1 })

    mockPost.mockResolvedValueOnce({ data: { ok: true } })
    const s = await mappingService.saveMappings(5, { foo: 'bar' })
    expect(mockPost).toHaveBeenCalledWith('/accounts/5/mappings', { mappings: { foo: 'bar' } })
    expect(s).toEqual({ ok: true })

    mockDelete.mockResolvedValueOnce({ data: { deleted: true } })
    const d = await mappingService.deleteMappings(5)
    expect(mockDelete).toHaveBeenCalledWith('/accounts/5/mappings')
    expect(d).toEqual({ deleted: true })
  })
})
