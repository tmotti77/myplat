import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { useSession, signOut } from 'next-auth/react'
import { useTranslation } from 'next-i18next'
import Link from 'next/link'
import Image from 'next/image'
import {
  Search,
  Home,
  FileText,
  Upload,
  Users,
  Settings,
  HelpCircle,
  LogOut,
  ChevronDown,
  ChevronRight,
  Building,
  User,
  Bell,
  Bookmark,
  BarChart3,
  Archive,
  Shield,
  Database,
  Zap,
  Brain,
  MessageSquare,
  Star,
  Calendar,
  Tag,
  Filter,
  Globe,
  Accessibility,
  Moon,
  Sun,
  Monitor,
  X,
  Menu,
  Check,
  UserPlus,
  Crown,
  Award,
  TrendingUp,
  Activity,
  Clock,
  Eye,
  Edit,
  Trash2,
  Share2,
  Download,
  Lock,
  Unlock,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle
} from '@/lib/icon-mappings'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useTheme } from '@/components/providers/theme-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  className?: string
}

interface NavigationItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  href?: string
  onClick?: () => void
  badge?: number
  children?: NavigationItem[]
  permissions?: string[]
  premium?: boolean
}

interface Tenant {
  id: string
  name: string
  logo?: string
  role: string
  permissions: string[]
  isOwner: boolean
  plan: 'free' | 'pro' | 'enterprise'
}

export function Sidebar({ isOpen, onClose, className }: SidebarProps) {
  const router = useRouter()
  const { data: session } = useSession()
  const { t } = useTranslation(['navigation', 'common'])
  const { theme, setTheme } = useTheme()
  const { direction } = useRTL()
  const { announceAction, preferences } = useAccessibility()

  const [expandedSections, setExpandedSections] = useState<string[]>(['main'])
  const [currentTenant, setCurrentTenant] = useState<Tenant | null>(null)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [showTenantSelector, setShowTenantSelector] = useState(false)
  const [notifications, setNotifications] = useState(0)

  // Load tenant data
  useEffect(() => {
    // Mock data - replace with API calls
    const mockTenants: Tenant[] = [
      {
        id: 'personal',
        name: 'Personal Workspace',
        role: 'owner',
        permissions: ['read', 'write', 'admin'],
        isOwner: true,
        plan: 'free'
      },
      {
        id: 'acme-corp',
        name: 'ACME Corporation',
        logo: '/images/tenants/acme.png',
        role: 'admin',
        permissions: ['read', 'write', 'manage_users'],
        isOwner: false,
        plan: 'enterprise'
      },
      {
        id: 'startup-inc',
        name: 'Startup Inc.',
        role: 'member',
        permissions: ['read', 'write'],
        isOwner: false,
        plan: 'pro'
      }
    ]

    setTenants(mockTenants)
    setCurrentTenant(mockTenants[0] || null)
    setNotifications(3) // Mock notification count
  }, [])

  // Navigation items configuration
  const navigationItems: NavigationItem[] = [
    {
      id: 'main',
      label: t('navigation:mainNavigation'),
      icon: Home,
      children: [
        {
          id: 'dashboard',
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
          id: 'collections',
          label: t('navigation:collections'),
          icon: Bookmark,
          href: '/collections'
        }
      ]
    },
    {
      id: 'content',
      label: t('navigation:contentManagement'),
      icon: Database,
      children: [
        {
          id: 'upload',
          label: t('navigation:upload'),
          icon: Upload,
          href: '/upload'
        },
        {
          id: 'processing',
          label: t('navigation:processing'),
          icon: Zap,
          href: '/processing',
          badge: 2
        },
        {
          id: 'archive',
          label: t('navigation:archive'),
          icon: Archive,
          href: '/archive'
        }
      ]
    },
    {
      id: 'ai',
      label: t('navigation:aiFeatures'),
      icon: Brain,
      children: [
        {
          id: 'chat',
          label: t('navigation:aiChat'),
          icon: MessageSquare,
          href: '/chat'
        },
        {
          id: 'insights',
          label: t('navigation:insights'),
          icon: TrendingUp,
          href: '/insights',
          premium: true
        },
        {
          id: 'recommendations',
          label: t('navigation:recommendations'),
          icon: Star,
          href: '/recommendations',
          premium: true
        }
      ]
    },
    {
      id: 'collaboration',
      label: t('navigation:collaboration'),
      icon: Users,
      children: [
        {
          id: 'team',
          label: t('navigation:team'),
          icon: Users,
          href: '/team',
          permissions: ['manage_users']
        },
        {
          id: 'sharing',
          label: t('navigation:sharing'),
          icon: Share2,
          href: '/sharing'
        },
        {
          id: 'activity',
          label: t('navigation:activity'),
          icon: Activity,
          href: '/activity'
        }
      ]
    },
    {
      id: 'analytics',
      label: t('navigation:analytics'),
      icon: BarChart3,
      children: [
        {
          id: 'usage',
          label: t('navigation:usage'),
          icon: BarChart3,
          href: '/analytics/usage',
          permissions: ['view_analytics']
        },
        {
          id: 'performance',
          label: t('navigation:performance'),
          icon: TrendingUp,
          href: '/analytics/performance',
          permissions: ['view_analytics']
        }
      ]
    }
  ]

  const bottomNavigationItems: NavigationItem[] = [
    {
      id: 'settings',
      label: t('navigation:settings'),
      icon: Settings,
      href: '/settings'
    },
    {
      id: 'help',
      label: t('navigation:help'),
      icon: HelpCircle,
      href: '/help'
    }
  ]

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => 
      prev.includes(sectionId)
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    )
    announceAction(
      expandedSections.includes(sectionId) 
        ? t('navigation:sectionCollapsed')
        : t('navigation:sectionExpanded'),
      'polite'
    )
  }

  const handleNavigation = (href: string, label: string) => {
    router.push(href)
    onClose()
    announceAction(t('navigation:navigatedTo', { page: label }), 'polite')
  }

  const handleTenantChange = (tenant: Tenant) => {
    setCurrentTenant(tenant)
    setShowTenantSelector(false)
    announceAction(t('navigation:tenantChanged', { tenant: tenant.name }), 'polite')
    // Here you would typically update the global state/context
  }

  const handleSignOut = async () => {
    await signOut({ callbackUrl: '/auth/signin' })
    announceAction(t('navigation:signedOut'), 'polite')
  }

  const hasPermission = (permissions?: string[]) => {
    if (!permissions || !currentTenant) return true
    return permissions.some(permission => 
      currentTenant.permissions.includes(permission)
    )
  }

  const isPremiumFeature = (premium?: boolean) => {
    if (!premium || !currentTenant) return false
    return currentTenant.plan === 'free'
  }

  const renderNavigationItem = (item: NavigationItem, level = 0) => {
    const isActive = router.pathname === item.href
    const isExpanded = expandedSections.includes(item.id)
    const hasChildren = item.children && item.children.length > 0
    const canAccess = hasPermission(item.permissions)
    const isPremium = isPremiumFeature(item.premium)

    if (!canAccess) return null

    const paddingClass = level === 0 ? 'ps-4' : 'ps-8'
    const itemClass = cn(
      'group flex items-center justify-between w-full text-start rounded-lg transition-colors',
      'focus-visible-ring',
      level === 0 ? 'px-3 py-2' : 'px-2 py-1.5',
      isActive
        ? 'bg-primary text-primary-foreground'
        : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
      isPremium && 'opacity-60'
    )

    const content = (
      <div className="flex items-center flex-1 min-w-0">
        <item.icon 
          className={cn(
            'flex-shrink-0',
            level === 0 ? 'w-5 h-5' : 'w-4 h-4',
            direction === 'rtl' ? 'ml-3' : 'mr-3'
          )}
          aria-hidden="true"
        />
        <span className="truncate">
          {item.label}
          {isPremium && (
            <Crown className="inline w-3 h-3 ms-1 text-yellow-500" aria-hidden="true" />
          )}
        </span>
        {item.badge && item.badge > 0 && (
          <span 
            className="bg-destructive text-destructive-foreground text-xs rounded-full px-2 py-0.5 ms-2"
            aria-label={t('navigation:badgeCount', { count: item.badge })}
          >
            {item.badge > 99 ? '99+' : item.badge}
          </span>
        )}
      </div>
    )

    if (hasChildren) {
      return (
        <div key={item.id}>
          <button
            onClick={() => toggleSection(item.id)}
            className={itemClass}
            aria-expanded={isExpanded}
            aria-controls={`section-${item.id}`}
          >
            {content}
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            ) : (
              <ChevronRight className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
            )}
          </button>
          <div
            id={`section-${item.id}`}
            className={cn(
              'mt-1 space-y-1',
              !isExpanded && 'hidden'
            )}
          >
            {item.children?.map(child => renderNavigationItem(child, level + 1))}
          </div>
        </div>
      )
    }

    if (item.href) {
      return (
        <Link
          key={item.id}
          href={item.href}
          onClick={(e) => {
            if (isPremium) {
              e.preventDefault()
              // Show premium upgrade modal
              return
            }
            handleNavigation(item.href!, item.label)
          }}
          className={itemClass}
          aria-current={isActive ? 'page' : undefined}
          aria-disabled={isPremium}
        >
          {content}
        </Link>
      )
    }

    if (item.onClick) {
      return (
        <button
          key={item.id}
          onClick={item.onClick}
          className={itemClass}
          disabled={isPremium}
        >
          {content}
        </button>
      )
    }

    return null
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden bg-black/20 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        id="sidebar-navigation"
        className={cn(
          'fixed top-0 start-0 z-50 w-64 h-full bg-sidebar border-e border-border',
          'transform transition-transform duration-300 ease-in-out lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'flex flex-col',
          className
        )}
        dir={direction}
        aria-label={t('navigation:sidebarNavigation')}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="truncate">
              <h2 className="text-sm font-semibold text-sidebar-foreground">
                {t('common:appName')}
              </h2>
              <p className="text-xs text-sidebar-muted">
                {currentTenant?.name}
              </p>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded-md hover:bg-sidebar-accent focus-visible-ring"
            aria-label={t('navigation:closeSidebar')}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tenant Selector */}
        <div className="p-4 border-b border-border">
          <div className="relative">
            <button
              onClick={() => setShowTenantSelector(!showTenantSelector)}
              className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-sidebar-accent focus-visible-ring"
              aria-expanded={showTenantSelector}
              aria-haspopup="listbox"
            >
              <div className="flex items-center space-x-2 min-w-0">
                {currentTenant?.logo ? (
                  <Image 
                    src={currentTenant.logo} 
                    alt="" 
                    width={20} 
                    height={20}
                    className="rounded"
                  />
                ) : (
                  <Building className="w-5 h-5 text-sidebar-muted" />
                )}
                <div className="text-start truncate">
                  <p className="text-sm font-medium text-sidebar-foreground truncate">
                    {currentTenant?.name}
                  </p>
                  <p className="text-xs text-sidebar-muted capitalize">
                    {currentTenant?.role} • {currentTenant?.plan}
                  </p>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-sidebar-muted" />
            </button>

            {showTenantSelector && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-popover border border-border rounded-lg shadow-lg z-10">
                <div className="p-1" role="listbox">
                  {tenants.map((tenant) => (
                    <button
                      key={tenant.id}
                      onClick={() => handleTenantChange(tenant)}
                      className="w-full flex items-center space-x-2 p-2 rounded-md hover:bg-accent focus-visible-ring text-start"
                      role="option"
                      aria-selected={currentTenant?.id === tenant.id}
                    >
                      {tenant.logo ? (
                        <Image 
                          src={tenant.logo} 
                          alt="" 
                          width={20} 
                          height={20}
                          className="rounded"
                        />
                      ) : (
                        <Building className="w-5 h-5 text-muted-foreground" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {tenant.name}
                        </p>
                        <p className="text-xs text-muted-foreground capitalize">
                          {tenant.role} • {tenant.plan}
                        </p>
                      </div>
                      {currentTenant?.id === tenant.id && (
                        <Check className="w-4 h-4 text-primary" />
                      )}
                    </button>
                  ))}
                </div>
                <div className="border-t border-border p-1">
                  <Link
                    href="/tenants/create"
                    className="w-full flex items-center space-x-2 p-2 rounded-md hover:bg-accent focus-visible-ring text-start"
                    onClick={onClose}
                  >
                    <UserPlus className="w-5 h-5 text-muted-foreground" />
                    <span className="text-sm">
                      {t('navigation:createWorkspace')}
                    </span>
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav 
          className="flex-1 overflow-y-auto p-4 space-y-2"
          aria-label={t('navigation:mainNavigation')}
        >
          {navigationItems.map(section => renderNavigationItem(section))}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-border p-4 space-y-2">
          {/* Theme toggle */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-sidebar-foreground">
              {t('navigation:theme')}
            </span>
            <div className="flex rounded-lg border border-border">
              <button
                onClick={() => setTheme('light')}
                className={cn(
                  'p-1 rounded-s-lg focus-visible-ring',
                  theme === 'light' ? 'bg-primary text-primary-foreground' : 'hover:bg-sidebar-accent'
                )}
                aria-label={t('navigation:lightTheme')}
              >
                <Sun className="w-4 h-4" />
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={cn(
                  'p-1 focus-visible-ring',
                  theme === 'dark' ? 'bg-primary text-primary-foreground' : 'hover:bg-sidebar-accent'
                )}
                aria-label={t('navigation:darkTheme')}
              >
                <Moon className="w-4 h-4" />
              </button>
              <button
                onClick={() => setTheme('system')}
                className={cn(
                  'p-1 rounded-e-lg focus-visible-ring',
                  theme === 'system' ? 'bg-primary text-primary-foreground' : 'hover:bg-sidebar-accent'
                )}
                aria-label={t('navigation:systemTheme')}
              >
                <Monitor className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Bottom navigation */}
          {bottomNavigationItems.map(item => renderNavigationItem(item))}

          {/* User profile */}
          <div className="pt-2 border-t border-border">
            <div className="flex items-center space-x-3 p-2 rounded-lg hover:bg-sidebar-accent">
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
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-sidebar-foreground truncate">
                  {session?.user?.name || t('navigation:guest')}
                </p>
                <p className="text-xs text-sidebar-muted truncate">
                  {session?.user?.email}
                </p>
              </div>
              <button
                onClick={handleSignOut}
                className="p-1 rounded hover:bg-sidebar-accent focus-visible-ring"
                aria-label={t('navigation:signOut')}
              >
                <LogOut className="w-4 h-4 text-sidebar-muted" />
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}