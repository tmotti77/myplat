import React, { createContext, useContext, useEffect, useState } from 'react'

interface AccessibilitySettings {
  reduceMotion: boolean
  highContrast: boolean
  largeText: boolean
  focusVisible: boolean
  announcements: boolean
  keyboardNavigation: boolean
  // Extended settings for accessibility menu
  fontSize: number
  zoomLevel: number
  reducedMotion: boolean  // Alias for reduceMotion
  enhancedFocus: boolean
  screenReaderMode: boolean
  audioDescriptions: boolean
  soundFeedback: boolean
  speechRate: number
  stickyKeys: boolean
  mouseKeys: boolean
  clickTimeout: number
  readingGuide: boolean
  dyslexiaFont: boolean
  contentPause: boolean
  simplifiedUI: boolean
  skipLinks: boolean
  landmarkNavigation: boolean
  headingNavigation: boolean
  autoSave: boolean
}

interface AccessibilityContextType {
  settings: AccessibilitySettings
  preferences: AccessibilitySettings  // Alias for settings
  updateSetting: (key: keyof AccessibilitySettings, value: boolean | number) => void
  updatePreferences: (updates: Partial<AccessibilitySettings>) => void  // Accepts partial settings object
  announce: (message: string, priority?: 'polite' | 'assertive') => void
  announceAction: (message: string, priority?: 'polite' | 'assertive') => void  // Announce user actions with optional priority
  isReducedMotion: boolean
  isHighContrast: boolean
  enableHighContrast: () => void
  disableHighContrast: () => void
  enableReducedMotion: () => void
  disableReducedMotion: () => void
  enableScreenReader: () => void
  disableScreenReader: () => void
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined)

const defaultSettings: AccessibilitySettings = {
  reduceMotion: false,
  highContrast: false,
  largeText: false,
  focusVisible: true,
  announcements: true,
  keyboardNavigation: true,
  // Extended settings defaults
  fontSize: 16,
  zoomLevel: 100,
  reducedMotion: false,
  enhancedFocus: false,
  screenReaderMode: false,
  audioDescriptions: false,
  soundFeedback: false,
  speechRate: 1.0,
  stickyKeys: false,
  mouseKeys: false,
  clickTimeout: 500,
  readingGuide: false,
  dyslexiaFont: false,
  contentPause: false,
  simplifiedUI: false,
  skipLinks: true,
  landmarkNavigation: true,
  headingNavigation: true,
  autoSave: false,
}

export function AccessibilityProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AccessibilitySettings>(defaultSettings)
  const [announcer, setAnnouncer] = useState<HTMLElement | null>(null)

  // Initialize settings from localStorage and system preferences
  useEffect(() => {
    const stored = localStorage.getItem('accessibility-settings')
    if (stored) {
      try {
        const parsedSettings = JSON.parse(stored)
        setSettings({ ...defaultSettings, ...parsedSettings })
      } catch {
        // Invalid stored settings, use defaults
      }
    }

    // Detect system preferences
    const mediaQueries = {
      reduceMotion: window.matchMedia('(prefers-reduced-motion: reduce)'),
      highContrast: window.matchMedia('(prefers-contrast: high)'),
    }

    const updateFromSystem = () => {
      setSettings(current => ({
        ...current,
        reduceMotion: current.reduceMotion || mediaQueries.reduceMotion.matches,
        highContrast: current.highContrast || mediaQueries.highContrast.matches,
      }))
    }

    updateFromSystem()

    // Listen for system preference changes
    Object.values(mediaQueries).forEach(mq => {
      mq.addListener(updateFromSystem)
    })

    return () => {
      Object.values(mediaQueries).forEach(mq => {
        mq.removeListener(updateFromSystem)
      })
    }
  }, [])

  // Create screen reader announcer
  useEffect(() => {
    const announcerElement = document.createElement('div')
    announcerElement.setAttribute('aria-live', 'polite')
    announcerElement.setAttribute('aria-atomic', 'true')
    announcerElement.className = 'sr-only'
    announcerElement.id = 'accessibility-announcer'
    document.body.appendChild(announcerElement)
    setAnnouncer(announcerElement)

    return () => {
      if (announcerElement.parentNode) {
        announcerElement.parentNode.removeChild(announcerElement)
      }
    }
  }, [])

  // Apply settings to document
  useEffect(() => {
    const root = document.documentElement

    // Reduce motion
    root.style.setProperty('--animation-duration', settings.reduceMotion ? '0.01ms' : '0.3s')
    root.classList.toggle('reduce-motion', settings.reduceMotion)

    // High contrast
    root.classList.toggle('high-contrast', settings.highContrast)

    // Large text
    if (settings.largeText) {
      root.style.fontSize = '1.125em'
    } else {
      root.style.fontSize = ''
    }

    // Focus visible
    root.classList.toggle('focus-visible-disabled', !settings.focusVisible)

    // Save to localStorage
    localStorage.setItem('accessibility-settings', JSON.stringify(settings))
  }, [settings])

  // Keyboard navigation setup
  useEffect(() => {
    if (!settings.keyboardNavigation) return

    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip navigation
      if (event.key === 'Tab') {
        document.body.classList.add('using-keyboard')
      }

      // Quick navigation shortcuts
      if (event.altKey) {
        switch (event.key) {
          case '1':
            event.preventDefault()
            const mainHeading = document.querySelector('h1')
            ;(mainHeading as HTMLElement)?.focus()
            break
          case '2':
            event.preventDefault()
            const navigation = document.querySelector('nav')
            ;(navigation as HTMLElement)?.focus()
            break
          case '3':
            event.preventDefault()
            const main = document.querySelector('main, [role="main"]')
            ;(main as HTMLElement)?.focus()
            break
          case '4':
            event.preventDefault()
            const search = document.querySelector('[role="search"], [type="search"]')
            ;(search as HTMLElement)?.focus()
            break
        }
      }
    }

    const handleMouseDown = () => {
      document.body.classList.remove('using-keyboard')
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousedown', handleMouseDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleMouseDown)
    }
  }, [settings.keyboardNavigation])

  const updateSetting = (key: keyof AccessibilitySettings, value: boolean | number) => {
    setSettings(current => ({
      ...current,
      [key]: value,
      // Sync reducedMotion with reduceMotion
      ...(key === 'reduceMotion' ? { reducedMotion: value } : {}),
      ...(key === 'reducedMotion' ? { reduceMotion: value } : {}),
    }))
  }

  const updatePreferences = (updates: Partial<AccessibilitySettings>) => {
    setSettings(current => ({
      ...current,
      ...updates,
      // Sync reducedMotion with reduceMotion
      ...('reduceMotion' in updates ? { reducedMotion: updates.reduceMotion } : {}),
      ...('reducedMotion' in updates ? { reduceMotion: updates.reducedMotion } : {}),
    }))
  }

  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!settings.announcements || !announcer) return

    announcer.setAttribute('aria-live', priority)
    announcer.textContent = message

    // Clear after announcement to allow repeated messages
    setTimeout(() => {
      announcer.textContent = ''
    }, 1000)
  }

  // Helper functions for specific accessibility features
  const announceAction = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announce(message, priority)
  }

  const enableHighContrast = () => updateSetting('highContrast', true)
  const disableHighContrast = () => updateSetting('highContrast', false)
  const enableReducedMotion = () => updateSetting('reduceMotion', true)
  const disableReducedMotion = () => updateSetting('reduceMotion', false)
  const enableScreenReader = () => updateSetting('announcements', true)
  const disableScreenReader = () => updateSetting('announcements', false)

  const value: AccessibilityContextType = {
    settings,
    preferences: settings,  // Alias
    updateSetting,
    updatePreferences,  // Accepts partial settings objects
    announce,
    announceAction,
    isReducedMotion: settings.reduceMotion,
    isHighContrast: settings.highContrast,
    enableHighContrast,
    disableHighContrast,
    enableReducedMotion,
    disableReducedMotion,
    enableScreenReader,
    disableScreenReader,
  }

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
      
      {/* Accessibility instructions overlay */}
      <div id="accessibility-instructions" className="sr-only">
        <h2>Keyboard Navigation Instructions</h2>
        <ul>
          <li>Tab: Navigate forward through interactive elements</li>
          <li>Shift + Tab: Navigate backward through interactive elements</li>
          <li>Enter/Space: Activate buttons and links</li>
          <li>Arrow keys: Navigate within menus and lists</li>
          <li>Escape: Close dialogs and menus</li>
          <li>Alt + 1: Jump to main heading</li>
          <li>Alt + 2: Jump to navigation</li>
          <li>Alt + 3: Jump to main content</li>
          <li>Alt + 4: Jump to search</li>
        </ul>
      </div>
    </AccessibilityContext.Provider>
  )
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext)
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider')
  }
  return context
}

// Hook for announcements
export function useAnnounce() {
  const { announce } = useAccessibility()
  return announce
}

// Hook for reduced motion preference
export function useReducedMotion() {
  const { isReducedMotion } = useAccessibility()
  return isReducedMotion
}

// Hook for high contrast preference
export function useHighContrast() {
  const { isHighContrast } = useAccessibility()
  return isHighContrast
}