/**
 * Test utilities and helpers
 */
import { render } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

/**
 * Render component with Router wrapper
 */
export function renderWithRouter(component, options = {}) {
  return render(
    <BrowserRouter>{component}</BrowserRouter>,
    options
  )
}

/**
 * Mock API response helper
 */
export function mockApiResponse(data, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  }
}

/**
 * Create mock account
 */
export function createMockAccount(overrides = {}) {
  return {
    id: 1,
    name: 'Test Account',
    bank_name: 'Test Bank',
    account_number: 'DE89370400440532013000',
    description: 'Test account',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

/**
 * Create mock category
 */
export function createMockCategory(overrides = {}) {
  return {
    id: 1,
    name: 'Test Category',
    color: '#3b82f6',
    icon: '🏷️',
    mappings: {
      recipients: [],
      purposes: [],
    },
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

/**
 * Create mock transaction
 */
export function createMockTransaction(overrides = {}) {
  return {
    id: 1,
    account_id: 1,
    date: '2024-01-01T00:00:00Z',
    recipient: 'Test Recipient',
    purpose: 'Test Purpose',
    amount: -50.00,
    category_id: null,
    row_hash: 'test_hash',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

/**
 * Wait for async operations
 */
export function waitFor(callback, timeout = 3000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now()
    const interval = setInterval(() => {
      try {
        const result = callback()
        if (result) {
          clearInterval(interval)
          resolve(result)
        }
      } catch (error) {
        // Continue waiting
      }
      
      if (Date.now() - startTime > timeout) {
        clearInterval(interval)
        reject(new Error('Timeout waiting for condition'))
      }
    }, 100)
  })
}
