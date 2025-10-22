import type { AppProps } from 'next/app'
import { SessionProvider } from 'next-auth/react'
import { ThemeProvider } from 'next-themes'
// import { appWithTranslation } from 'next-i18next'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import { Toaster } from 'react-hot-toast'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import Head from 'next/head'

// Styles
import '../src/styles/globals.css'

// Components
import { ErrorBoundary } from '@/components/error-boundary'
import { LoadingProvider } from '@/components/providers/loading-provider'
import { AccessibilityProvider } from '@/components/providers/accessibility-provider'
import { RTLProvider } from '@/components/providers/rtl-provider'
import { ProgressBar } from '@/components/ui/progress-bar'

// Hooks
import { useDirection } from '@/hooks/use-direction'
import { AuthProvider } from '@/hooks/use-auth'

// Utils
import { cn } from '@/lib/utils'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors except 408, 429
        if (error?.status >= 400 && error?.status < 500 && ![408, 429].includes(error?.status)) {
          return false
        }
        return failureCount < 3
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

function MyApp({ Component, pageProps: { session, ...pageProps } }: AppProps) {
  const router = useRouter()
  const { locale } = router
  const direction = useDirection(locale)
  const [isLoading, setIsLoading] = useState(false)

  // Handle route change loading
  useEffect(() => {
    const handleStart = () => setIsLoading(true)
    const handleComplete = () => setIsLoading(false)

    router.events.on('routeChangeStart', handleStart)
    router.events.on('routeChangeComplete', handleComplete)
    router.events.on('routeChangeError', handleComplete)

    return () => {
      router.events.off('routeChangeStart', handleStart)
      router.events.off('routeChangeComplete', handleComplete)
      router.events.off('routeChangeError', handleComplete)
    }
  }, [router])

  // Set document direction and language
  useEffect(() => {
    document.documentElement.dir = direction
    document.documentElement.lang = locale || 'en'
  }, [direction, locale])

  // Keyboard navigation enhancement
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip link activation
      if (event.key === 'Tab' && !event.shiftKey) {
        const skipLink = document.querySelector('.skip-link') as HTMLElement
        if (skipLink && document.activeElement === document.body) {
          skipLink.focus()
        }
      }

      // Global keyboard shortcuts
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'k':
            event.preventDefault()
            // Open command palette
            const searchButton = document.querySelector('[data-search-trigger]') as HTMLElement
            searchButton?.click()
            break
          case '/':
            event.preventDefault()
            // Focus search
            const searchInput = document.querySelector('[data-search-input]') as HTMLElement
            searchInput?.focus()
            break
        }
      }

      // Escape key handling
      if (event.key === 'Escape') {
        // Close modals, dropdowns, etc.
        const closeButtons = document.querySelectorAll('[data-close-on-escape]')
        closeButtons.forEach(button => (button as HTMLElement).click())
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <>
      <Head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="theme-color" content="#000000" />
        <meta name="color-scheme" content="light dark" />
        
        {/* Preconnect to important domains */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        
        {/* Favicons */}
        <link rel="icon" href="/favicon.ico" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
        
        {/* PWA meta tags */}
        <meta name="application-name" content="Hybrid RAG Platform" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="RAG Platform" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="msapplication-TileColor" content="#000000" />
        <meta name="msapplication-tap-highlight" content="no" />
        
        {/* Security headers */}
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-Frame-Options" content="DENY" />
        <meta httpEquiv="X-XSS-Protection" content="1; mode=block" />
        
        {/* Performance hints */}
        <link rel="dns-prefetch" href="//api.myplatform.com" />
        <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="/fonts/heebo-var.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="/fonts/noto-arabic-var.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
      </Head>

      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <SessionProvider session={session}>
            <ThemeProvider
              attribute="class"
              defaultTheme="system"
              enableSystem
              disableTransitionOnChange={false}
            >
              <AccessibilityProvider>
                <RTLProvider>
                  <LoadingProvider>
                    <AuthProvider>
                      <div
                        className={cn(
                          'min-h-screen bg-background font-sans antialiased',
                          direction === 'rtl' && 'font-hebrew',
                          locale === 'ar' && 'font-arabic'
                        )}
                        dir={direction}
                      >
                      {/* Skip to main content link */}
                      <a
                        href="#main-content"
                        className="skip-link focus-visible-ring"
                      >
                        Skip to main content
                      </a>

                      {/* Progress bar for route changes */}
                      {isLoading && <ProgressBar />}

                      {/* Main application */}
                      <Component {...pageProps} />

                      {/* Toast notifications */}
                      <Toaster
                        position={direction === 'rtl' ? 'bottom-left' : 'bottom-right'}
                        toastOptions={{
                          duration: 4000,
                          className: cn(
                            'bg-background text-foreground border border-border',
                            'shadow-elevated rounded-lg'
                          ),
                          success: {
                            className: 'bg-success text-success-foreground',
                          },
                          error: {
                            className: 'bg-destructive text-destructive-foreground',
                          },
                        }}
                      />

                      {/* Development tools */}
                      {process.env.NODE_ENV === 'development' && (
                        <ReactQueryDevtools initialIsOpen={false} />
                      )}
                      
                      {/* Analytics and performance monitoring */}
                      {process.env.NODE_ENV === 'production' && (
                        <>
                          <Analytics />
                          <SpeedInsights />
                        </>
                      )}
                      </div>
                    </AuthProvider>
                  </LoadingProvider>
                </RTLProvider>
              </AccessibilityProvider>
            </ThemeProvider>
          </SessionProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    </>
  )
}

export default MyApp // appWithTranslation(MyApp)