import React from 'react'
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Input from '../../components/common/Input'
import { describe, it, expect } from 'vitest'

describe('Input component', () => {
  it('renders label and input and shows error text', () => {
    render(<Input label="Name" error="Required" defaultValue="abc" />)

    // Label
    expect(screen.getByText('Name')).toBeInTheDocument()

    // Input (role textbox)
    const input = screen.getByRole('textbox')
    expect(input).toBeInTheDocument()
    expect(input).toHaveValue('abc')

    // Error
    expect(screen.getByText('Required')).toBeInTheDocument()
  })
})
