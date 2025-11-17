import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// mock the store used by the hook
const mockShowToast = vi.fn(() => 123)
const mockShowSuccess = vi.fn()
const mockShowError = vi.fn()
const mockShowWarning = vi.fn()
const mockShowInfo = vi.fn()

vi.mock('../../store', () => ({
  useUIStore: () => ({
    showToast: mockShowToast,
    showSuccess: mockShowSuccess,
    showError: mockShowError,
    showWarning: mockShowWarning,
    showInfo: mockShowInfo,
  })
}))

import useToast from '../../hooks/useToast'

function TestComp() {
  const { showToast, showSuccess, showError, showWarning, showInfo } = useToast()

  return (
    <div>
      <button onClick={() => showToast('hi', 'info', 1000)}>toast</button>
      <button onClick={() => showSuccess('ok')}>success</button>
      <button onClick={() => showError('err')}>error</button>
      <button onClick={() => showWarning('warn')}>warn</button>
      <button onClick={() => showInfo('info')}>info</button>
    </div>
  )
}

describe('useToast hook', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('calls underlying store methods', () => {
    render(<TestComp />)

    fireEvent.click(screen.getByText('toast'))
    expect(mockShowToast).toHaveBeenCalledWith({ message: 'hi', type: 'info', duration: 1000 })

    fireEvent.click(screen.getByText('success'))
    expect(mockShowSuccess).toHaveBeenCalledWith('ok')

    fireEvent.click(screen.getByText('error'))
    expect(mockShowError).toHaveBeenCalledWith('err')

    fireEvent.click(screen.getByText('warn'))
    expect(mockShowWarning).toHaveBeenCalledWith('warn')

    fireEvent.click(screen.getByText('info'))
    expect(mockShowInfo).toHaveBeenCalledWith('info')
  })
})
