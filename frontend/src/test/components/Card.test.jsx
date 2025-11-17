import React from 'react'
import '@testing-library/jest-dom'
import { render, screen, fireEvent } from '@testing-library/react'
import Card from '../../components/common/Card'
import { describe, it, expect, vi } from 'vitest'

describe('Card component', () => {
  it('renders title, subtitle and footer', () => {
    render(
      <Card title="My Title" subtitle="Sub" footer={<div>Footer</div>}>
        Content
      </Card>
    )

    expect(screen.getByText('My Title')).toBeInTheDocument()
    expect(screen.getByText('Sub')).toBeInTheDocument()
    expect(screen.getByText('Footer')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders as a button and calls onClick when clickable', () => {
    const onClick = vi.fn()
    const { container } = render(
      <Card clickable onClick={onClick} title="Clickable">
        Clickable content
      </Card>
    )

    const btn = container.querySelector('button')
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(onClick).toHaveBeenCalled()
  })
})
