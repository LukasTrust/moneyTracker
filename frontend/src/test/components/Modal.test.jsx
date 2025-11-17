import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, fireEvent } from '@testing-library/react'
import Modal, { ConfirmDialog } from '../../components/common/Modal'
import { describe, it, expect, vi } from 'vitest'

describe('Modal component', () => {
  it('renders dialog and title when open', () => {
    const onClose = vi.fn()
    render(
      <Modal isOpen={true} onClose={onClose} title="Modal Title">
        Body Content
      </Modal>
    )

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Modal Title')).toBeInTheDocument()
    expect(screen.getByText('Body Content')).toBeInTheDocument()

    // Close button should be present and call onClose
    const btn = screen.getByRole('button', { name: /schließen/i })
    fireEvent.click(btn)
    expect(onClose).toHaveBeenCalled()
  })

  it('ConfirmDialog triggers onConfirm and onCancel', () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()

    render(
      <ConfirmDialog
        isOpen={true}
        onConfirm={onConfirm}
        onCancel={onCancel}
        title="Confirm"
        message="Are you sure?"
        confirmText="Yes"
        cancelText="No"
      />
    )

    expect(screen.getByText('Are you sure?')).toBeInTheDocument()

    const yes = screen.getByText('Yes')
    const no = screen.getByText('No')
    fireEvent.click(yes)
    fireEvent.click(no)

    expect(onConfirm).toHaveBeenCalled()
    expect(onCancel).toHaveBeenCalled()
  })
})
