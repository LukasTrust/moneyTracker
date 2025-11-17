import React from 'react'
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import LoadingSpinner, { Skeleton, SkeletonLines, SkeletonCard } from '../../components/common/LoadingSpinner'
import { describe, it, expect } from 'vitest'

describe('LoadingSpinner component', () => {
  it('renders an SVG spinner by default', () => {
    const { container } = render(<LoadingSpinner />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('shows text when the text prop is provided', () => {
    render(<LoadingSpinner text="Lädt..." />)
    expect(screen.getByText('Lädt...')).toBeInTheDocument()
  })

  it('renders fullScreen wrapper when fullScreen is true', () => {
    const { container } = render(<LoadingSpinner fullScreen text="Vollbild" />)
    // the full screen wrapper uses the Tailwind class `fixed`
    const fixedEl = container.querySelector('.fixed')
    expect(fixedEl).toBeInTheDocument()
    expect(screen.getByText('Vollbild')).toBeInTheDocument()
  })
})

describe('Skeleton components', () => {
  it('Skeleton renders with passed className', () => {
    const { container } = render(<Skeleton className="my-test-class" data-testid="skeleton" />)
    expect(container.querySelector('.my-test-class')).toBeInTheDocument()
  })

  it('SkeletonLines renders the requested number of lines', () => {
    const count = 4
    const { container } = render(<SkeletonLines count={count} />)
    // Skeletons use the `animate-pulse` class
    const lines = container.querySelectorAll('.animate-pulse')
    expect(lines.length).toBe(count)
  })

  it('SkeletonCard renders structure with skeletons', () => {
    const { container } = render(<SkeletonCard />)
    // expect at least one animate-pulse element inside the card
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })
})
