import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { useTranslation } from 'next-i18next'
import Link from 'next/link'
import {
  Home,
  Search,
  FileText,
  Upload,
  Users,
  Bell,
  MessageSquare,
  BarChart3,
  Bookmark,
  Plus,
  Brain,
  Settings,
  User,
  Menu,
  X,
  ChevronUp,
  Activity,
  Clock,
  Star,
  Archive,
  Share2,
  Database,
  Zap,
  TrendingUp,
  Calendar,
  Tag,
  Filter,
  Grid3X3,
  List,
  Heart,
  Award,
  Crown,
  Shield,
  HelpCircle,
  Layers,
  Command,
  Globe,
  Languages,
  Accessibility,
  Volume2,
  Eye,
  Type,
  Contrast,
  MousePointer,
  Keyboard,
  Focus
} from '@/lib/icon-mappings'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface MobileNavigationProps {
  className?: string
}

interface NavigationItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  href: string
  badge?: number
  premium?: boolean
  shortcut?: string
}

interface QuickAction {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  action: () => void
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'destructive'
}

export function MobileNavigation({ className }: MobileNavigationProps) {
  const router = useRouter()
  const { t } = useTranslation(['navigation', 'common'])
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [showQuickActions, setShowQuickActions] = useState(false)
  const [lastScrollY, setLastScrollY] = useState(0)
  const [isVisible, setIsVisible] = useState(true)

  // Primary navigation items
  const navigationItems: NavigationItem[] = [
    {
      id: 'home',
      label: t('navigation:dashboard'),
      icon: Home,
      href: '/'
    },
    {
      id: 'search',
      label: t('navigation:search'),
      icon: Search,
      href: '/search'
    },
    {
      id: 'documents',
      label: t('navigation:documents'),
      icon: FileText,
      href: '/documents',
      badge: 12
    },
    {
      id: 'more',
      label: t('navigation:more'),
      icon: Menu,
      href: '#',
      shortcut: 'menu'
    }
  ]

  // Quick actions that appear when tapping the "+" button
  const quickActions: QuickAction[] = [
    {
      id: 'upload',
      label: t('navigation:uploadDocument'),
      icon: Upload,
      action: () => router.push('/upload'),
      color: 'primary'
    },
    {
      id: 'chat',
      label: t('navigation:startChat'),
      icon: MessageSquare,
      action: () => router.push('/chat'),
      color: 'secondary'
    },
    {
      id: 'collection',
      label: t('navigation:createCollection'),
      icon: Bookmark,
      action: () => router.push('/collections/new'),
      color: 'success'
    },
    {
      id: 'scan',
      label: t('navigation:scanDocument'),
      icon: Camera,
      action: () => {
        // Open camera for document scanning
        if ('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices) {
          router.push('/scan')
        } else {
          // Fallback to upload
          router.push('/upload')
        }
      },
      color: 'warning'
    }
  ]

  // Hide/show navigation based on scroll direction
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY
      
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down - hide navigation
        setIsVisible(false)
      } else {
        // Scrolling up - show navigation
        setIsVisible(true)
      }
      
      setLastScrollY(currentScrollY)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [lastScrollY])

  const handleNavigation = (item: NavigationItem) => {
    if (item.id === 'more') {
      // Toggle more menu or quick actions
      setShowQuickActions(!showQuickActions)
      announceAction(
        showQuickActions 
          ? t('navigation:quickActionsHidden')
          : t('navigation:quickActionsShown'),
        'polite'
      )
    } else {
      router.push(item.href)
      announceAction(t('navigation:navigatedTo', { page: item.label }), 'polite')
    }
  }

  const handleQuickAction = (action: QuickAction) => {
    action.action()
    setShowQuickActions(false)
    announceAction(t('navigation:actionTriggered', { action: action.label }), 'polite')
  }

  const isActive = (href: string) => {
    if (href === '/') {
      return router.pathname === '/'
    }
    return router.pathname.startsWith(href)
  }

  const getActionColor = (color?: QuickAction['color']) => {
    switch (color) {
      case 'primary': return 'bg-primary text-primary-foreground'
      case 'secondary': return 'bg-secondary text-secondary-foreground'
      case 'success': return 'bg-green-500 text-white'
      case 'warning': return 'bg-yellow-500 text-white'
      case 'destructive': return 'bg-destructive text-destructive-foreground'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  return (
    <>
      {/* Quick Actions Overlay */}
      {showQuickActions && (
        <>
          <div 
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
            onClick={() => setShowQuickActions(false)}
            aria-hidden="true"
          />
          
          <div 
            className="fixed bottom-20 start-1/2 transform -translate-x-1/2 z-50"
            role="dialog"
            aria-label={t('navigation:quickActions')}
          >
            <div className="flex flex-col items-center space-y-3 p-4">
              {quickActions.map((action, index) => {
                const Icon = action.icon
                return (
                  <button
                    key={action.id}
                    onClick={() => handleQuickAction(action)}
                    className={cn(
                      'flex items-center justify-center w-14 h-14 rounded-full shadow-lg',
                      'transform transition-all duration-200 hover:scale-110 focus-visible-ring',
                      getActionColor(action.color),
                      'animate-in slide-in-from-bottom-2 fade-in-0',
                    )}
                    style={{
                      animationDelay: `${index * 50}ms`,
                      animationFillMode: 'both'
                    }}
                    aria-label={action.label}
                    title={action.label}
                  >
                    <Icon className="w-6 h-6" />
                  </button>
                )
              })}
              
              {/* Action labels */}
              <div className="bg-popover border border-border rounded-lg px-3 py-2 max-w-xs">
                <p className="text-xs text-center text-muted-foreground">
                  {t('navigation:tapToPerformAction')}
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Mobile Navigation Bar */}
      <nav
        className={cn(
          'fixed bottom-0 start-0 end-0 z-30 bg-background/95 backdrop-blur border-t border-border',
          'supports-[backdrop-filter]:bg-background/80',
          'transform transition-transform duration-300 ease-in-out',
          isVisible ? 'translate-y-0' : 'translate-y-full',
          className
        )}
        dir={direction}
        aria-label={t('navigation:mobileNavigation')}
      >
        <div className="flex items-center justify-around px-2 py-2 safe-area-inset-bottom">
          {navigationItems.map((item) => {
            const Icon = item.icon
            const active = item.href !== '#' && isActive(item.href)

            return (
              <button
                key={item.id}
                onClick={() => handleNavigation(item)}
                className={cn(
                  'flex flex-col items-center justify-center min-w-0 flex-1 px-2 py-2 rounded-lg',
                  'transition-colors duration-200 focus-visible-ring',
                  active
                    ? 'text-primary bg-primary/10'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )}
                aria-current={active ? 'page' : undefined}
                aria-label={
                  item.badge && item.badge > 0
                    ? t('navigation:itemWithBadge', { item: item.label, count: item.badge })
                    : item.label
                }
              >
                <div className="relative">
                  <Icon className="w-5 h-5" />
                  {item.badge && item.badge > 0 && (
                    <span className="absolute -top-2 -end-2 bg-destructive text-destructive-foreground text-xs rounded-full w-4 h-4 flex items-center justify-center">
                      {item.badge > 9 ? '9+' : item.badge}
                    </span>
                  )}
                  {item.id === 'more' && showQuickActions && (
                    <div className="absolute -top-1 -end-1 w-2 h-2 bg-primary rounded-full animate-pulse" />
                  )}
                </div>
                <span className="text-xs mt-1 truncate w-full text-center">
                  {item.label}
                </span>
              </button>
            )
          })}
        </div>

        {/* Safe area for devices with home indicator */}
        <div className="h-safe-area-inset-bottom bg-background/95" />

        {/* Visual indicator for swipe gestures */}
        <div className="absolute top-0 start-1/2 transform -translate-x-1/2 w-8 h-1 bg-muted-foreground/20 rounded-full" />
      </nav>

      {/* Floating Action Button (alternative design) */}
      <button
        onClick={() => setShowQuickActions(!showQuickActions)}
        className={cn(
          'fixed bottom-20 end-4 w-14 h-14 bg-primary text-primary-foreground rounded-full shadow-lg',
          'flex items-center justify-center transition-all duration-300 focus-visible-ring z-40',
          'hover:scale-110 active:scale-95',
          showQuickActions && 'rotate-45',
          !isVisible && 'translate-y-20 opacity-0 pointer-events-none'
        )}
        aria-label={
          showQuickActions 
            ? t('navigation:closeQuickActions')
            : t('navigation:openQuickActions')
        }
        aria-expanded={showQuickActions}
      >
        <Plus className="w-6 h-6" />
      </button>

      {/* Haptic feedback for supported devices */}
      <style jsx global>{`
        @supports (backdrop-filter: blur(10px)) {
          .mobile-nav {
            backdrop-filter: blur(10px);
          }
        }
        
        /* Handle safe areas for modern mobile devices */
        @supports (padding: max(0px)) {
          .safe-area-inset-bottom {
            padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
          }
          
          .h-safe-area-inset-bottom {
            height: env(safe-area-inset-bottom);
          }
        }

        /* Hide on print */
        @media print {
          nav[aria-label*="mobile"] {
            display: none !important;
          }
        }

        /* Reduce motion for accessibility */
        @media (prefers-reduced-motion: reduce) {
          .mobile-nav * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }
      `}</style>
    </>
  )
}

// Camera icon component (since it's not in lucide-react by default)
function Camera({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  )
}