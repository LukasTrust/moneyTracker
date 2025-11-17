import React from 'react'
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Button from '../../components/common/Button'
import { describe, it, expect } from 'vitest'

describe('Button component', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('shows a spinner when loading is true', () => {
    const { container } = render(<Button loading>Save</Button>)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('applies fullWidth class when fullWidth is true', () => {
    const { container } = render(<Button fullWidth>Full</Button>)
    expect(container.querySelector('.w-full')).toBeInTheDocument()
  })
})
