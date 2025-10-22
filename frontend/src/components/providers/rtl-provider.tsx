import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/router'

type Direction = 'ltr' | 'rtl'

interface RTLContextType {
  direction: Direction
  isRTL: boolean
  setDirection: (direction: Direction) => void
  toggleDirection: () => void
  getLocalizedDirection: (locale?: string) => Direction
}

const RTLContext = createContext<RTLContextType | undefined>(undefined)

// Languages that use RTL
const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur', 'yi', 'iw', 'ji', 'arc', 'dv']

export function RTLProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [direction, setDirectionState] = useState<Direction>('ltr')

  // Get direction based on locale
  const getLocalizedDirection = (locale?: string): Direction => {
    const lang = locale || router.locale || 'en'
    return RTL_LANGUAGES.includes(lang) ? 'rtl' : 'ltr'
  }

  // Initialize direction based on locale
  useEffect(() => {
    const newDirection = getLocalizedDirection(router.locale)
    setDirectionState(newDirection)
  }, [router.locale])

  // Apply direction to document
  useEffect(() => {
    document.documentElement.dir = direction
    document.documentElement.dataset.direction = direction
    
    // Update CSS custom properties for RTL-aware styling
    document.documentElement.style.setProperty('--reading-direction', direction)
    document.documentElement.style.setProperty('--start', direction === 'rtl' ? 'right' : 'left')
    document.documentElement.style.setProperty('--end', direction === 'rtl' ? 'left' : 'right')
    
    // Add/remove RTL class for Tailwind variants
    document.documentElement.classList.toggle('rtl', direction === 'rtl')
    document.documentElement.classList.toggle('ltr', direction === 'ltr')
  }, [direction])

  // Handle locale changes
  useEffect(() => {
    const handleRouteChange = () => {
      const newDirection = getLocalizedDirection(router.locale)
      setDirectionState(newDirection)
    }

    router.events.on('routeChangeComplete', handleRouteChange)
    return () => {
      router.events.off('routeChangeComplete', handleRouteChange)
    }
  }, [router.events, router.locale])

  // Enhanced keyboard navigation for RTL
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Override arrow key behavior for RTL layouts
      if (direction === 'rtl') {
        const target = event.target as HTMLElement
        const isInputField = target.matches('input, textarea, [contenteditable]')
        
        if (!isInputField) {
          switch (event.key) {
            case 'ArrowLeft':
              // In RTL, left arrow should move forward
              event.preventDefault()
              const nextElement = target.nextElementSibling as HTMLElement
              nextElement?.focus()
              break
            case 'ArrowRight':
              // In RTL, right arrow should move backward
              event.preventDefault()
              const prevElement = target.previousElementSibling as HTMLElement
              prevElement?.focus()
              break
          }
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [direction])

  const setDirection = (newDirection: Direction) => {
    setDirectionState(newDirection)
    
    // Optionally store user preference
    if (typeof window !== 'undefined') {
      localStorage.setItem('user-direction-preference', newDirection)
    }
  }

  const toggleDirection = () => {
    setDirection(direction === 'ltr' ? 'rtl' : 'ltr')
  }

  const value: RTLContextType = {
    direction,
    isRTL: direction === 'rtl',
    setDirection,
    toggleDirection,
    getLocalizedDirection,
  }

  return (
    <RTLContext.Provider value={value}>
      <style jsx global>{`
        /* RTL-aware CSS custom properties */
        :root {
          --reading-direction: ${direction};
          --start: ${direction === 'rtl' ? 'right' : 'left'};
          --end: ${direction === 'rtl' ? 'left' : 'right'};
          --transform-translate-x: ${direction === 'rtl' ? '-' : ''}1;
        }
        
        /* RTL-aware animations */
        @keyframes slideInFromStart {
          from {
            transform: translateX(calc(var(--transform-translate-x) * 100%));
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        @keyframes slideInFromEnd {
          from {
            transform: translateX(calc(var(--transform-translate-x) * -100%));
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        /* RTL-aware focus indicators */
        [dir="rtl"] .focus-ring-offset {
          box-shadow: 0 0 0 2px var(--background), 0 0 0 4px var(--ring);
        }
        
        /* RTL-aware scrollbar positioning */
        [dir="rtl"] ::-webkit-scrollbar {
          direction: rtl;
        }
        
        /* RTL-aware text selection */
        [dir="rtl"] ::selection {
          direction: rtl;
        }
        
        /* RTL-aware tooltips and popovers */
        [dir="rtl"] [data-tooltip] {
          text-align: ${direction === 'rtl' ? 'right' : 'left'};
        }
        
        /* RTL-aware form layouts */
        [dir="rtl"] .form-group {
          text-align: right;
        }
        
        [dir="rtl"] .form-label {
          text-align: right;
        }
        
        /* RTL-aware navigation */
        [dir="rtl"] .nav-item:first-child {
          border-radius: 0 0.375rem 0.375rem 0;
        }
        
        [dir="rtl"] .nav-item:last-child {
          border-radius: 0.375rem 0 0 0.375rem;
        }
        
        /* RTL-aware breadcrumbs */
        [dir="rtl"] .breadcrumb-item::before {
          content: "\\";
          transform: scaleX(-1);
        }
        
        /* RTL-aware dropdown menus */
        [dir="rtl"] .dropdown-menu {
          text-align: right;
        }
        
        /* RTL-aware progress bars */
        [dir="rtl"] .progress-bar {
          direction: rtl;
        }
        
        /* RTL-aware table headers */
        [dir="rtl"] .table-header {
          text-align: right;
        }
        
        /* RTL-aware code blocks */
        [dir="rtl"] .code-block {
          direction: ltr;
          text-align: left;
        }
        
        /* RTL-aware mathematical expressions */
        [dir="rtl"] .math-expression {
          direction: ltr;
          text-align: left;
          display: inline-block;
        }
        
        /* RTL-aware timestamps and dates */
        [dir="rtl"] .timestamp {
          direction: ltr;
          text-align: left;
          display: inline-block;
        }
        
        /* RTL-aware URL and email displays */
        [dir="rtl"] .url,
        [dir="rtl"] .email {
          direction: ltr;
          text-align: left;
          display: inline-block;
        }
      `}</style>
      {children}
    </RTLContext.Provider>
  )
}

export function useRTL() {
  const context = useContext(RTLContext)
  if (context === undefined) {
    throw new Error('useRTL must be used within an RTLProvider')
  }
  return context
}

// Utility hook for direction-aware class names
export function useDirectionalClassName(baseClass: string, rtlClass?: string, ltrClass?: string) {
  const { direction } = useRTL()
  
  if (direction === 'rtl' && rtlClass) {
    return `${baseClass} ${rtlClass}`
  }
  
  if (direction === 'ltr' && ltrClass) {
    return `${baseClass} ${ltrClass}`
  }
  
  return baseClass
}

// Utility hook for direction-aware values
export function useDirectionalValue<T>(ltrValue: T, rtlValue: T): T {
  const { isRTL } = useRTL()
  return isRTL ? rtlValue : ltrValue
}

// Utility hook for direction-aware positioning
export function useDirectionalPosition() {
  const { direction, isRTL } = useRTL()
  
  return {
    start: isRTL ? 'right' : 'left',
    end: isRTL ? 'left' : 'right',
    direction,
    isRTL,
    // Helper functions
    translateX: (value: number) => `translateX(${isRTL ? -value : value}px)`,
    marginStart: (value: string) => ({ [isRTL ? 'marginRight' : 'marginLeft']: value }),
    marginEnd: (value: string) => ({ [isRTL ? 'marginLeft' : 'marginRight']: value }),
    paddingStart: (value: string) => ({ [isRTL ? 'paddingRight' : 'paddingLeft']: value }),
    paddingEnd: (value: string) => ({ [isRTL ? 'paddingLeft' : 'paddingRight']: value }),
    borderStart: (value: string) => ({ [isRTL ? 'borderRight' : 'borderLeft']: value }),
    borderEnd: (value: string) => ({ [isRTL ? 'borderLeft' : 'borderRight']: value }),
    textAlign: isRTL ? 'right' : 'left',
    float: (side: 'start' | 'end') => (side === 'start' ? (isRTL ? 'right' : 'left') : (isRTL ? 'left' : 'right')),
  }
}