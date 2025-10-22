import { ReactNode, useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/router'
import { useTranslation } from 'next-i18next'

// Components
import { Sidebar } from './sidebar'
import { Header } from './header'
import { MobileNavigation } from './mobile-navigation'
import { Footer } from './footer'
import { CommandPalette } from '@/components/command-palette'
import { NotificationCenter } from '@/components/notifications/notification-center'
import { AccessibilityMenu } from '@/components/accessibility/accessibility-menu-simple'

// Hooks
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface MainLayoutProps {
  children: ReactNode
  title?: string
  description?: string
  fullWidth?: boolean
  hideFooter?: boolean
  className?: string
}

export function MainLayout({
  children,
  title,
  description,
  fullWidth = false,
  hideFooter = false,
  className,
}: MainLayoutProps) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const { t } = useTranslation(['common', 'navigation'])
  const { announce } = useAccessibility()
  const { direction } = useRTL()

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [accessibilityMenuOpen, setAccessibilityMenuOpen] = useState(false)

  // Keyboard shortcuts
  useKeyboardShortcuts({
    'cmd+k': () => setCommandPaletteOpen(true),
    'cmd+/': () => setCommandPaletteOpen(true),
    escape: () => {
      setCommandPaletteOpen(false)
      setNotificationsOpen(false)
      setAccessibilityMenuOpen(false)
    },
    'alt+1': () => {
      const mainHeading = document.querySelector('h1')
      mainHeading?.focus()
      announce(t('navigation:jumpedToMainHeading'), 'polite')
    },
    'alt+2': () => {
      const nav = document.querySelector('nav[aria-label="Main navigation"]')
      ;(nav as HTMLElement)?.focus()
      announce(t('navigation:jumpedToNavigation'), 'polite')
    },
    'alt+3': () => {
      const main = document.querySelector('main')
      main?.focus()
      announce(t('navigation:jumpedToMainContent'), 'polite')
    },
    'alt+a': () => setAccessibilityMenuOpen(true),
    'alt+n': () => setNotificationsOpen(true),
  })

  // Close sidebar on route change
  useEffect(() => {
    const handleRouteChange = () => {
      setSidebarOpen(false)
    }

    router.events.on('routeChangeStart', handleRouteChange)
    return () => router.events.off('routeChangeStart', handleRouteChange)
  }, [router.events])

  // Responsive sidebar handling
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setSidebarOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Loading state
  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="spinner w-8 h-8 mx-auto" />
          <p className="text-muted-foreground">{t('common:loading')}</p>
        </div>
      </div>
    )
  }

  // Unauthenticated state
  if (status === 'unauthenticated' && router.pathname !== '/auth/signin') {
    router.push('/auth/signin')
    return null
  }

  return (
    <div className={cn('min-h-screen bg-background', className)} dir={direction}>
      {/* Skip links for screen readers */}
      <a
        href="#main-content"
        className="skip-link focus-visible-ring"
      >
        {t('navigation:skipToMainContent')}
      </a>
      <a
        href="#sidebar-navigation"
        className="skip-link focus-visible-ring"
      >
        {t('navigation:skipToNavigation')}
      </a>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />
        </div>
      )}

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        className="z-50"
      />

      {/* Main content area */}
      <div className="lg:ps-64">
        {/* Header */}
        <Header
          onMenuClick={() => setSidebarOpen(true)}
          onCommandClick={() => setCommandPaletteOpen(true)}
          onNotificationsClick={() => setNotificationsOpen(true)}
          onAccessibilityClick={() => setAccessibilityMenuOpen(true)}
          title={title}
        />

        {/* Main content */}
        <main
          id="main-content"
          className={cn(
            'min-h-screen pb-16',
            !fullWidth && 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'
          )}
          tabIndex={-1}
          role="main"
          aria-label={t('navigation:mainContent')}
        >
          {title && (
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground">
                {title}
              </h1>
              {description && (
                <p className="mt-2 text-muted-foreground">
                  {description}
                </p>
              )}
            </div>
          )}
          
          {children}
        </main>

        {/* Footer */}
        {!hideFooter && <Footer />}
      </div>

      {/* Mobile navigation */}
      <MobileNavigation className="lg:hidden" />

      {/* Command Palette */}
      <CommandPalette
        open={commandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
      />

      {/* Notification Center */}
      <NotificationCenter
        open={notificationsOpen}
        onOpenChange={setNotificationsOpen}
      />

      {/* Accessibility Menu */}
      <AccessibilityMenu
        open={accessibilityMenuOpen}
        onOpenChange={setAccessibilityMenuOpen}
      />

      {/* Floating action button for accessibility */}
      <button
        onClick={() => setAccessibilityMenuOpen(true)}
        className="fab w-14 h-14 no-print focus-visible-ring"
        aria-label={t('navigation:accessibilityOptions')}
        title={t('navigation:accessibilityOptions')}
      >
        <span className="sr-only">{t('navigation:accessibilityOptions')}</span>
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
          />
        </svg>
      </button>

      {/* Live region for announcements */}
      <div
        id="live-region"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      />

      {/* Print styles */}
      <style jsx global>{`
        @media print {
          .no-print {
            display: none !important;
          }
          
          .print-break-before {
            page-break-before: always;
          }
          
          .print-break-after {
            page-break-after: always;
          }
          
          .print-break-inside-avoid {
            page-break-inside: avoid;
          }
        }
      `}</style>
    </div>
  )
}

// Higher-order component for pages that need authentication
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  const AuthenticatedComponent = (props: P) => {
    const { status } = useSession()
    const router = useRouter()

    useEffect(() => {
      if (status === 'unauthenticated') {
        router.push('/auth/signin')
      }
    }, [status, router])

    if (status === 'loading') {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="spinner w-8 h-8" />
        </div>
      )
    }

    if (status === 'unauthenticated') {
      return null
    }

    return <Component {...props} />
  }

  AuthenticatedComponent.displayName = `withAuth(${Component.displayName || Component.name})`
  return AuthenticatedComponent
}