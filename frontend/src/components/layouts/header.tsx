import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useTranslation } from 'next-i18next'
import { useRouter } from 'next/router'
import Image from 'next/image'
import Link from 'next/link'
import {
  Search,
  Bell,
  Settings,
  User,
  Menu,
  Globe,
  Moon,
  Sun,
  Monitor,
  Accessibility,
  Command,
  HelpCircle,
  LogOut,
  ChevronDown,
  Plus,
  Filter,
  Clock,
  TrendingUp,
  Star,
  Archive,
  Share2,
  Download,
  Edit,
  Trash2,
  MoreHorizontal,
  Keyboard,
  Languages,
  Palette,
  Volume2,
  Eye,
  MousePointer,
  Type,
  Contrast,
  Focus,
  Navigation,
  Zap,
  FileText,
  Users,
  BarChart3,
  Database,
  Brain,
  MessageSquare,
  Upload,
  Bookmark,
  Tag,
  Calendar,
  Activity,
  Shield,
  Key,
  CreditCard,
  Crown,
  Award,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  X,
  Check
} from '@/lib/icon-mappings'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useTheme } from '@/components/providers/theme-provider'
import { useRTL } from '@/components/providers/rtl-provider'
import { useDebounce } from '@/hooks/use-debounce'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'

// Utils
import { cn } from '@/lib/utils'

interface HeaderProps {
  onMenuClick: () => void
  onCommandClick: () => void
  onNotificationsClick: () => void
  onAccessibilityClick: () => void
  title?: string
  className?: string
}

interface SearchSuggestion {
  id: string
  type: 'document' | 'collection' | 'action' | 'user' | 'recent'
  title: string
  description?: string
  icon: React.ComponentType<{ className?: string }>
  href?: string
  action?: () => void
  metadata?: {
    lastModified?: string
    author?: string
    tags?: string[]
    confidence?: number
  }
}

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  actionUrl?: string
  actionLabel?: string
}

export function Header({
  onMenuClick,
  onCommandClick,
  onNotificationsClick,
  onAccessibilityClick,
  title,
  className
}: HeaderProps) {
  const { data: session } = useSession()
  const { t } = useTranslation(['navigation', 'common', 'search'])
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const { direction, setDirection } = useRTL()
  const { announceAction, preferences } = useAccessibility()

  const [searchQuery, setSearchQuery] = useState('')
  const [searchFocused, setSearchFocused] = useState(false)
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isSearchLoading, setIsSearchLoading] = useState(false)

  const searchInputRef = useRef<HTMLInputElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)

  const debouncedSearchQuery = useDebounce(searchQuery, 300)

  // Keyboard shortcuts
  useKeyboardShortcuts({
    'cmd+k': () => {
      searchInputRef.current?.focus()
      announceAction(t('search:searchFocused'), 'polite')
    },
    'cmd+/': () => {
      searchInputRef.current?.focus()
    },
    escape: () => {
      if (searchFocused) {
        searchInputRef.current?.blur()
        setSearchQuery('')
        setSuggestions([])
      }
      setShowUserMenu(false)
    },
    'cmd+n': () => {
      onNotificationsClick()
    },
    'alt+u': () => {
      setShowUserMenu(!showUserMenu)
    }
  })

  // Load notifications
  useEffect(() => {
    // Mock notifications data
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'success',
        title: t('navigation:documentProcessed'),
        message: 'Annual Report 2024.pdf has been successfully processed and indexed.',
        timestamp: '2 minutes ago',
        read: false,
        actionUrl: '/documents/annual-report-2024',
        actionLabel: t('navigation:viewDocument')
      },
      {
        id: '2',
        type: 'info',
        title: t('navigation:newTeamMember'),
        message: 'Sarah Johnson has joined your workspace as an Editor.',
        timestamp: '1 hour ago',
        read: false,
        actionUrl: '/team',
        actionLabel: t('navigation:viewTeam')
      },
      {
        id: '3',
        type: 'warning',
        title: t('navigation:storageLimit'),
        message: 'You are approaching your storage limit (85% used).',
        timestamp: '3 hours ago',
        read: true,
        actionUrl: '/settings/billing',
        actionLabel: t('navigation:upgradePlan')
      }
    ]

    setNotifications(mockNotifications)
    setUnreadCount(mockNotifications.filter(n => !n.read).length)
  }, [t])

  // Search suggestions
  useEffect(() => {
    if (!debouncedSearchQuery.trim()) {
      setSuggestions([])
      setIsSearchLoading(false)
      return
    }

    setIsSearchLoading(true)

    // Mock search suggestions
    const mockSuggestions: SearchSuggestion[] = [
      {
        id: 'doc-1',
        type: 'document',
        title: 'Product Requirements Document',
        description: 'Detailed specifications for the new dashboard feature',
        icon: FileText,
        href: '/documents/prd-dashboard',
        metadata: {
          lastModified: '2 days ago',
          author: 'John Doe',
          tags: ['product', 'requirements'],
          confidence: 0.95
        }
      },
      {
        id: 'collection-1',
        type: 'collection',
        title: 'Marketing Materials',
        description: '24 documents',
        icon: Bookmark,
        href: '/collections/marketing-materials'
      },
      {
        id: 'action-1',
        type: 'action',
        title: 'Upload new document',
        description: 'Add files to your workspace',
        icon: Upload,
        action: () => router.push('/upload')
      },
      {
        id: 'user-1',
        type: 'user',
        title: 'Sarah Johnson',
        description: 'Product Manager',
        icon: User,
        href: '/team/sarah-johnson'
      }
    ]

    // Simulate API delay
    setTimeout(() => {
      setSuggestions(mockSuggestions.filter(s => 
        s.title.toLowerCase().includes(debouncedSearchQuery.toLowerCase()) ||
        s.description?.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
      ))
      setIsSearchLoading(false)
    }, 150)
  }, [debouncedSearchQuery, router])

  // Click outside handlers
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setSearchFocused(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`)
      setSearchFocused(false)
      announceAction(t('search:searchSubmitted'), 'polite')
    }
  }

  const handleSuggestionSelect = (suggestion: SearchSuggestion) => {
    if (suggestion.href) {
      router.push(suggestion.href)
    } else if (suggestion.action) {
      suggestion.action()
    }
    setSearchFocused(false)
    setSearchQuery('')
    setSuggestions([])
    announceAction(t('search:suggestionSelected', { title: suggestion.title }), 'polite')
  }

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success': return CheckCircle
      case 'warning': return AlertTriangle
      case 'error': return XCircle
      default: return Info
    }
  }

  const getNotificationColor = (type: Notification['type']) => {
    switch (type) {
      case 'success': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'error': return 'text-red-500'
      default: return 'text-blue-500'
    }
  }

  return (
    <header 
      className={cn(
        'sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border',
        'supports-[backdrop-filter]:bg-background/60',
        className
      )}
      dir={direction}
    >
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left section */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md hover:bg-accent focus-visible-ring"
            aria-label={t('navigation:openMenu')}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Breadcrumb / Title */}
          {title && (
            <div className="hidden sm:block">
              <h1 className="text-lg font-semibold text-foreground">
                {title}
              </h1>
            </div>
          )}
        </div>

        {/* Center section - Search */}
        <div 
          ref={searchRef}
          className="flex-1 max-w-2xl mx-4 relative"
        >
          <form onSubmit={handleSearchSubmit}>
            <div className="relative">
              <Search className="absolute start-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                ref={searchInputRef}
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                placeholder={t('search:globalSearchPlaceholder')}
                className="w-full ps-10 pe-12 py-2 bg-muted rounded-lg border border-border focus:border-primary focus:ring-1 focus:ring-primary focus:bg-background"
                aria-label={t('search:globalSearch')}
                aria-expanded={searchFocused && (suggestions.length > 0 || searchQuery.length > 0)}
                aria-haspopup="listbox"
                autoComplete="off"
              />
              <div className="absolute end-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                {isSearchLoading && (
                  <div className="w-4 h-4 border-2 border-muted-foreground border-t-transparent rounded-full animate-spin" />
                )}
                <kbd className="hidden sm:inline-flex px-1.5 py-0.5 text-xs bg-muted-foreground/10 rounded">
                  ⌘K
                </kbd>
              </div>
            </div>
          </form>

          {/* Search suggestions dropdown */}
          {searchFocused && (suggestions.length > 0 || searchQuery.length > 0) && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-popover border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
              {suggestions.length > 0 ? (
                <div className="p-1" role="listbox">
                  {suggestions.map((suggestion, index) => {
                    const Icon = suggestion.icon
                    return (
                      <button
                        key={suggestion.id}
                        onClick={() => handleSuggestionSelect(suggestion)}
                        className="w-full flex items-start space-x-3 p-3 rounded-md hover:bg-accent focus-visible-ring text-start"
                        role="option"
                        aria-selected={false}
                      >
                        <Icon className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium truncate">
                              {suggestion.title}
                            </p>
                            {suggestion.metadata?.confidence && (
                              <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                                {Math.round(suggestion.metadata.confidence * 100)}%
                              </span>
                            )}
                          </div>
                          {suggestion.description && (
                            <p className="text-xs text-muted-foreground truncate">
                              {suggestion.description}
                            </p>
                          )}
                          {suggestion.metadata && (
                            <div className="flex items-center space-x-2 mt-1">
                              {suggestion.metadata.lastModified && (
                                <span className="text-xs text-muted-foreground">
                                  {suggestion.metadata.lastModified}
                                </span>
                              )}
                              {suggestion.metadata.author && (
                                <span className="text-xs text-muted-foreground">
                                  by {suggestion.metadata.author}
                                </span>
                              )}
                              {suggestion.metadata.tags && (
                                <div className="flex space-x-1">
                                  {suggestion.metadata.tags.slice(0, 2).map(tag => (
                                    <span 
                                      key={tag}
                                      className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>
              ) : searchQuery.length > 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">
                    {t('search:noResults')}
                  </p>
                  <button
                    onClick={() => router.push(`/search?q=${encodeURIComponent(searchQuery)}`)}
                    className="mt-2 text-primary hover:underline text-sm focus-visible-ring rounded"
                  >
                    {t('search:searchAllDocuments')}
                  </button>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Right section */}
        <div className="flex items-center space-x-2">
          {/* Quick actions */}
          <button
            onClick={onCommandClick}
            className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-muted rounded-lg hover:bg-muted/80 focus-visible-ring"
            aria-label={t('navigation:commandPalette')}
          >
            <Command className="w-4 h-4" />
            <span className="text-sm text-muted-foreground">
              {t('navigation:commands')}
            </span>
          </button>

          {/* Theme toggle */}
          <div className="hidden sm:flex rounded-lg border border-border">
            <button
              onClick={() => setTheme('light')}
              className={cn(
                'p-2 rounded-s-lg focus-visible-ring',
                theme === 'light' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              )}
              aria-label={t('navigation:lightTheme')}
              title={t('navigation:lightTheme')}
            >
              <Sun className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={cn(
                'p-2 focus-visible-ring',
                theme === 'dark' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              )}
              aria-label={t('navigation:darkTheme')}
              title={t('navigation:darkTheme')}
            >
              <Moon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTheme('system')}
              className={cn(
                'p-2 rounded-e-lg focus-visible-ring',
                theme === 'system' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              )}
              aria-label={t('navigation:systemTheme')}
              title={t('navigation:systemTheme')}
            >
              <Monitor className="w-4 h-4" />
            </button>
          </div>

          {/* Language toggle */}
          <button
            onClick={() => setDirection(direction === 'ltr' ? 'rtl' : 'ltr')}
            className="p-2 rounded-lg hover:bg-accent focus-visible-ring"
            aria-label={t('navigation:toggleDirection')}
            title={t('navigation:toggleDirection')}
          >
            <Languages className="w-4 h-4" />
          </button>

          {/* Accessibility menu */}
          <button
            onClick={onAccessibilityClick}
            className="p-2 rounded-lg hover:bg-accent focus-visible-ring"
            aria-label={t('navigation:accessibilityOptions')}
            title={t('navigation:accessibilityOptions')}
          >
            <Accessibility className="w-4 h-4" />
          </button>

          {/* Notifications */}
          <button
            onClick={onNotificationsClick}
            className="relative p-2 rounded-lg hover:bg-accent focus-visible-ring"
            aria-label={
              unreadCount > 0 
                ? t('navigation:notificationsWithCount', { count: unreadCount })
                : t('navigation:notifications')
            }
            title={t('navigation:notifications')}
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -end-1 bg-destructive text-destructive-foreground text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* User menu */}
          <div ref={userMenuRef} className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-1 rounded-lg hover:bg-accent focus-visible-ring"
              aria-expanded={showUserMenu}
              aria-haspopup="menu"
              aria-label={t('navigation:userMenu')}
            >
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                {session?.user?.image ? (
                  <Image
                    src={session.user.image}
                    alt={session.user.name || 'User'}
                    width={32}
                    height={32}
                    className="rounded-full"
                  />
                ) : (
                  <User className="w-4 h-4 text-primary-foreground" />
                )}
              </div>
              <ChevronDown className="w-3 h-3 text-muted-foreground" />
            </button>

            {showUserMenu && (
              <div className="absolute top-full end-0 mt-1 w-64 bg-popover border border-border rounded-lg shadow-lg z-50">
                {/* User info */}
                <div className="p-4 border-b border-border">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                      {session?.user?.image ? (
                        <Image
                          src={session.user.image}
                          alt={session.user.name || 'User'}
                          width={40}
                          height={40}
                          className="rounded-full"
                        />
                      ) : (
                        <User className="w-5 h-5 text-primary-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {session?.user?.name || t('navigation:guest')}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {session?.user?.email}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Menu items */}
                <div className="p-1" role="menu">
                  <Link
                    href="/profile"
                    className="flex items-center space-x-3 w-full px-3 py-2 rounded-md hover:bg-accent focus-visible-ring text-start"
                    role="menuitem"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <User className="w-4 h-4" />
                    <span className="text-sm">
                      {t('navigation:profile')}
                    </span>
                  </Link>
                  
                  <Link
                    href="/settings"
                    className="flex items-center space-x-3 w-full px-3 py-2 rounded-md hover:bg-accent focus-visible-ring text-start"
                    role="menuitem"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <Settings className="w-4 h-4" />
                    <span className="text-sm">
                      {t('navigation:settings')}
                    </span>
                  </Link>

                  <Link
                    href="/help"
                    className="flex items-center space-x-3 w-full px-3 py-2 rounded-md hover:bg-accent focus-visible-ring text-start"
                    role="menuitem"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <HelpCircle className="w-4 h-4" />
                    <span className="text-sm">
                      {t('navigation:help')}
                    </span>
                  </Link>

                  <div className="border-t border-border my-1" />

                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      // Handle sign out
                    }}
                    className="flex items-center space-x-3 w-full px-3 py-2 rounded-md hover:bg-accent focus-visible-ring text-start"
                    role="menuitem"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm">
                      {t('navigation:signOut')}
                    </span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}