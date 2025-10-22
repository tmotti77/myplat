/**
 * useKeyboardShortcuts Hook
 * 
 * Manages keyboard shortcuts and hotkey functionality
 */

import { useEffect, useCallback, useRef } from 'react'

interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  metaKey?: boolean
  action: () => void
  description?: string
  preventDefault?: boolean
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[]
  enabled?: boolean
  target?: HTMLElement | Document
}

export function useKeyboardShortcuts({
  shortcuts,
  enabled = true,
  target = document
}: UseKeyboardShortcutsOptions) {
  const shortcutsRef = useRef(shortcuts)
  
  // Update shortcuts ref when shortcuts change
  useEffect(() => {
    shortcutsRef.current = shortcuts
  }, [shortcuts])

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return

    const { key, ctrlKey, shiftKey, altKey, metaKey } = event
    
    const matchingShortcut = shortcutsRef.current.find(shortcut => {
      return (
        shortcut.key.toLowerCase() === key.toLowerCase() &&
        !!shortcut.ctrlKey === ctrlKey &&
        !!shortcut.shiftKey === shiftKey &&
        !!shortcut.altKey === altKey &&
        !!shortcut.metaKey === metaKey
      )
    })

    if (matchingShortcut) {
      if (matchingShortcut.preventDefault !== false) {
        event.preventDefault()
      }
      matchingShortcut.action()
    }
  }, [enabled])

  useEffect(() => {
    if (!enabled) return

    const targetElement = target as EventTarget
    targetElement.addEventListener('keydown', handleKeyDown)

    return () => {
      targetElement.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown, enabled, target])

  // Helper function to register a single shortcut
  const registerShortcut = useCallback((shortcut: KeyboardShortcut) => {
    shortcutsRef.current = [...shortcutsRef.current, shortcut]
  }, [])

  // Helper function to unregister a shortcut
  const unregisterShortcut = useCallback((key: string) => {
    shortcutsRef.current = shortcutsRef.current.filter(
      shortcut => shortcut.key !== key
    )
  }, [])

  return {
    registerShortcut,
    unregisterShortcut,
    shortcuts: shortcutsRef.current
  }
}

// Common keyboard shortcuts
export const COMMON_SHORTCUTS = {
  SEARCH: { key: 'k', ctrlKey: true, description: 'Open search' },
  COMMAND_PALETTE: { key: 'k', ctrlKey: true, shiftKey: true, description: 'Open command palette' },
  ESCAPE: { key: 'Escape', description: 'Close modal/dialog' },
  ENTER: { key: 'Enter', description: 'Confirm action' },
  SAVE: { key: 's', ctrlKey: true, description: 'Save' },
  UNDO: { key: 'z', ctrlKey: true, description: 'Undo' },
  REDO: { key: 'y', ctrlKey: true, description: 'Redo' },
  COPY: { key: 'c', ctrlKey: true, description: 'Copy' },
  PASTE: { key: 'v', ctrlKey: true, description: 'Paste' },
  SELECT_ALL: { key: 'a', ctrlKey: true, description: 'Select all' },
  NEW: { key: 'n', ctrlKey: true, description: 'New' },
  HELP: { key: '?', shiftKey: true, description: 'Show help' }
} as const

export default useKeyboardShortcuts