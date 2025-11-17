import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useUIStore, TOAST_TYPES, MODAL_TYPES } from '../../store/uiStore'

describe('uiStore', () => {
  beforeEach(() => {
    // reset store to known state
    useUIStore.setState({
      toasts: [],
      activeModal: null,
      modalData: null,
      sidebarOpen: true,
      globalLoading: false,
    })
    vi.useRealTimers()
  })

  it('can show and remove toast, auto-remove after duration', () => {
    vi.useFakeTimers()

    const id = useUIStore.getState().showToast({ message: 'Hi', type: TOAST_TYPES.INFO, duration: 1000 })
    let state = useUIStore.getState()
    expect(state.toasts.length).toBe(1)
    expect(state.toasts[0].message).toBe('Hi')

    // advance timers so auto-remove runs
    vi.advanceTimersByTime(1000)
    // run pending timers
    vi.runOnlyPendingTimers()

    state = useUIStore.getState()
    expect(state.toasts.find(t => t.id === id)).toBeUndefined()
    vi.useRealTimers()
  })

  it('showSuccess/showError/showWarning/showInfo add toasts', () => {
    const s = useUIStore.getState()
    s.showSuccess('ok')
    s.showError('err')
    s.showWarning('warn')
    s.showInfo('info')

    const state = useUIStore.getState()
    expect(state.toasts.length).toBe(4)
  })

  it('removeToast and clearToasts work', () => {
    const s = useUIStore.getState()
    const id1 = s.showToast({ message: 'a', duration: 0 })
    const id2 = s.showToast({ message: 'b', duration: 0 })
    expect(useUIStore.getState().toasts.length).toBe(2)

    s.removeToast(id1)
    expect(useUIStore.getState().toasts.length).toBe(1)

    s.clearToasts()
    expect(useUIStore.getState().toasts.length).toBe(0)
  })

  it('openModal/closeModal set modal state', () => {
    const s = useUIStore.getState()
    s.openModal(MODAL_TYPES.CONFIRM, { foo: 'bar' })
    expect(useUIStore.getState().activeModal).toBe(MODAL_TYPES.CONFIRM)
    expect(useUIStore.getState().modalData).toEqual({ foo: 'bar' })

    s.closeModal()
    expect(useUIStore.getState().activeModal).toBeNull()
  })

  it('toggleSidebar and setSidebar work', () => {
    const s = useUIStore.getState()
    const before = s.sidebarOpen
    s.toggleSidebar()
    expect(useUIStore.getState().sidebarOpen).toBe(!before)
    s.setSidebar(true)
    expect(useUIStore.getState().sidebarOpen).toBe(true)
  })

  it('setGlobalLoading updates flag', () => {
    const s = useUIStore.getState()
    s.setGlobalLoading(true)
    expect(useUIStore.getState().globalLoading).toBe(true)
  })
})
