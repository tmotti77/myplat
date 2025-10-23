import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'next-i18next'
import { useRouter } from 'next/router'
import { formatDistanceToNow } from 'date-fns'
import { enUS, he, ar } from 'date-fns/locale'
import Image from 'next/image'
import Link from 'next/link'
import {
  Bell,
  BellRing,
  X,
  Check,
  CheckCheck,
  Trash2,
  Settings,
  Filter,
  Search,
  MoreHorizontal,
  Eye,
  EyeOff,
  Archive,
  Star,
  Heart,
  Share2,
  MessageSquare,
  User,
  Users,
  FileText,
  Upload,
  Download,
  Calendar,
  Clock,
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Zap,
  Brain,
  Crown,
  Award,
  Trophy,
  Shield,
  Lock,
  Unlock,
  Key,
  Mail,
  Phone,
  Globe,
  MapPin,
  Target,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Database,
  Server,
  HardDrive,
  Cpu,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Headphones,
  Speaker,
  Mic,
  Volume2,
  VolumeX,
  Music,
  Video,
  Image as ImageIcon,
  Camera,
  Film,
  Play,
  Pause,
  Square,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
  Shuffle,
  Repeat,
  Radio,
  Podcast,
  Code,
  Terminal,
  GitBranch,
  Package,
  Folder,
  FolderPlus,
  File,
  FilePlus,
  FileImage,
  FileVideo,
  FileAudio,
  FileSpreadsheet,
  FileBarChart,
  Copy,
  Cut,
  Paste,
  Scissors,
  Paperclip,
  Link as LinkIcon,
  ExternalLink,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  ArrowUpLeft,
  ArrowDownLeft,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsUp,
  ChevronsDown,
  ChevronsLeft,
  ChevronsRight,
  CornerUpLeft,
  CornerUpRight,
  CornerDownLeft,
  CornerDownRight,
  Move,
  RotateCcw,
  RotateCw,
  RefreshCw,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  Focus,
  Crosshair,
  Scan,
  QrCode,
  Wifi,
  WifiOff,
  Bluetooth,
  Battery,
  BatteryLow,
  Power,
  PowerOff,
  Plug,
  PlugZap,
  Cable,
  Usb,
  Save,
  SaveAll,
  FolderOpen,
  FolderClosed,
  Trash,
  Delete,
  Backspace,
  Plus,
  Minus,
  HelpCircle,
  QuestionMark,
  Exclamation,
  Hash,
  AtSign,
  Percent,
  DollarSign,
  Euro,
  Pound,
  Yen,
  Bitcoin,
  CreditCard,
  Banknote,
  Coins,
  Wallet,
  PiggyBank,
  ShoppingCart,
  ShoppingBag,
  Gift,
  GiftCard,
  Tag,
  Tags,
  Label,
  Ticket,
  Receipt,
  Invoice,
  Bookmark,
  BookmarkPlus,
  BookmarkMinus,
  BookmarkCheck,
  BookmarkX,
  Flag,
  FlagTriangleLeft,
  FlagTriangleRight,
  Flame,
  Lightning,
  Bolt,
  Rocket,
  Airplane,
  Car,
  Truck,
  Bus,
  Train,
  Ship,
  Anchor,
  Compass,
  Navigation,
  Map,
  Route,
  Home,
  Building,
  Store,
  Factory,
  School,
  University,
  Hospital,
  Church,
  Landmark,
  Castle,
  Bridge,
  Tower,
  Mountain,
  Tree,
  Flower,
  Sun,
  Moon,
  Star as StarIcon,
  Cloud,
  CloudRain,
  CloudSnow,
  Snowflake,
  Umbrella,
  Wind,
  Thermometer,
  Droplets,
  Waves,
  Sparkles,
  Gem,
  Diamond
} from '@/lib/icon-mappings'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface NotificationCenterProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  className?: string
}

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error' | 'system' | 'social' | 'ai' | 'security'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  title: string
  message: string
  description?: string
  timestamp: Date
  read: boolean
  starred: boolean
  archived: boolean
  category: 'document' | 'team' | 'system' | 'ai' | 'security' | 'billing' | 'general'
  sender?: {
    id: string
    name: string
    avatar?: string
    role?: string
  }
  target?: {
    id: string
    type: 'document' | 'collection' | 'user' | 'page'
    name: string
    href?: string
  }
  actions?: Array<{
    id: string
    label: string
    type: 'primary' | 'secondary' | 'destructive'
    action: () => void | Promise<void>
    href?: string
  }>
  metadata?: {
    deviceInfo?: string
    location?: string
    ipAddress?: string
    tags?: string[]
    confidence?: number
    duration?: string
    size?: string
  }
  interactive?: boolean
  persistent?: boolean
  sound?: boolean
  vibration?: boolean
  badge?: string
  groupId?: string
}

interface NotificationGroup {
  id: string
  title: string
  notifications: Notification[]
  collapsed: boolean
}

export function NotificationCenter({ open, onOpenChange, className }: NotificationCenterProps) {
  const { t } = useTranslation(['notifications', 'common'])
  const router = useRouter()
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [notifications, setNotifications] = useState<Notification[]>([])
  const [filteredNotifications, setFilteredNotifications] = useState<Notification[]>([])
  const [selectedFilter, setSelectedFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([])
  const [showArchived, setShowArchived] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [groups, setGroups] = useState<NotificationGroup[]>([])

  const containerRef = useRef<HTMLDivElement>(null)

  // Get appropriate locale for date formatting
  const getDateLocale = () => {
    switch (router.locale) {
      case 'he': return he
      case 'ar': return ar
      default: return enUS
    }
  }

  // Mock notifications data
  useEffect(() => {
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'success',
        priority: 'high',
        title: t('notifications:documentProcessed'),
        message: 'Annual Report 2024.pdf has been successfully processed and indexed.',
        description: 'The document is now searchable and ready for AI analysis.',
        timestamp: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
        read: false,
        starred: false,
        archived: false,
        category: 'document',
        target: {
          id: 'doc-1',
          type: 'document',
          name: 'Annual Report 2024.pdf',
          href: '/documents/annual-report-2024'
        },
        actions: [
          {
            id: 'view-document',
            label: t('notifications:viewDocument'),
            type: 'primary',
            action: async () => { await router.push('/documents/annual-report-2024') }
          },
          {
            id: 'start-analysis',
            label: t('notifications:startAnalysis'),
            type: 'secondary',
            action: async () => { await router.push('/documents/annual-report-2024?action=analyze') }
          }
        ],
        metadata: {
          size: '2.4 MB',
          confidence: 0.95,
          tags: ['report', 'financial', '2024']
        },
        interactive: true,
        sound: true
      },
      {
        id: '2',
        type: 'info',
        priority: 'medium',
        title: t('notifications:newTeamMember'),
        message: 'Sarah Johnson has joined your workspace as a Product Manager.',
        timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
        read: false,
        starred: false,
        archived: false,
        category: 'team',
        sender: {
          id: 'admin-1',
          name: 'System Admin',
          role: 'Administrator'
        },
        target: {
          id: 'user-sarah',
          type: 'user',
          name: 'Sarah Johnson',
          href: '/team/sarah-johnson'
        },
        actions: [
          {
            id: 'view-profile',
            label: t('notifications:viewProfile'),
            type: 'primary',
            action: async () => { await router.push('/team/sarah-johnson') }
          },
          {
            id: 'send-welcome',
            label: t('notifications:sendWelcome'),
            type: 'secondary',
            action: async () => {
              // Send welcome message
              announceAction(t('notifications:welcomeSent'), 'polite')
            }
          }
        ],
        metadata: {
          location: 'San Francisco, CA'
        },
        interactive: true
      },
      {
        id: '3',
        type: 'warning',
        priority: 'high',
        title: t('notifications:storageLimit'),
        message: 'You are approaching your storage limit (85% used).',
        description: 'Consider upgrading your plan or archiving old documents.',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        read: true,
        starred: true,
        archived: false,
        category: 'billing',
        actions: [
          {
            id: 'upgrade-plan',
            label: t('notifications:upgradePlan'),
            type: 'primary',
            action: async () => { await router.push('/settings/billing') }
          },
          {
            id: 'manage-storage',
            label: t('notifications:manageStorage'),
            type: 'secondary',
            action: async () => { await router.push('/settings/storage') }
          }
        ],
        metadata: {
          size: '8.5 GB / 10 GB'
        },
        persistent: true,
        interactive: true
      },
      {
        id: '4',
        type: 'ai',
        priority: 'medium',
        title: t('notifications:aiInsightReady'),
        message: 'AI analysis completed for Market Research Q4 document.',
        description: 'New insights and recommendations are available.',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
        read: false,
        starred: false,
        archived: false,
        category: 'ai',
        target: {
          id: 'analysis-1',
          type: 'document',
          name: 'Market Research Q4',
          href: '/insights/market-research-q4'
        },
        actions: [
          {
            id: 'view-insights',
            label: t('notifications:viewInsights'),
            type: 'primary',
            action: async () => { await router.push('/insights/market-research-q4') }
          }
        ],
        metadata: {
          confidence: 0.88,
          duration: '2.3 minutes'
        },
        badge: 'AI',
        interactive: true
      },
      {
        id: '5',
        type: 'security',
        priority: 'urgent',
        title: t('notifications:suspiciousLogin'),
        message: 'Login detected from an unrecognized device.',
        description: 'If this wasn\'t you, please secure your account immediately.',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
        read: false,
        starred: false,
        archived: false,
        category: 'security',
        actions: [
          {
            id: 'secure-account',
            label: t('notifications:secureAccount'),
            type: 'destructive',
            action: async () => { await router.push('/settings/security') }
          },
          {
            id: 'was-me',
            label: t('notifications:wasMe'),
            type: 'secondary',
            action: async () => {
              // Mark as recognized
              announceAction(t('notifications:deviceRecognized'), 'polite')
            }
          }
        ],
        metadata: {
          deviceInfo: 'iPhone 15 Pro',
          location: 'New York, NY',
          ipAddress: '192.168.1.100'
        },
        persistent: true,
        interactive: true,
        sound: true,
        vibration: true
      },
      {
        id: '6',
        type: 'social',
        priority: 'low',
        title: t('notifications:documentShared'),
        message: 'Design Guidelines has been shared with you.',
        timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000), // 12 hours ago
        read: true,
        starred: false,
        archived: false,
        category: 'document',
        sender: {
          id: 'user-mike',
          name: 'Mike Chen',
          avatar: '/avatars/mike.jpg',
          role: 'Developer'
        },
        target: {
          id: 'doc-guidelines',
          type: 'document',
          name: 'Design Guidelines',
          href: '/documents/design-guidelines'
        },
        actions: [
          {
            id: 'open-document',
            label: t('notifications:openDocument'),
            type: 'primary',
            action: async () => { await router.push('/documents/design-guidelines') }
          }
        ],
        groupId: 'shared-documents'
      },
      {
        id: '7',
        type: 'system',
        priority: 'low',
        title: t('notifications:maintenanceScheduled'),
        message: 'Scheduled maintenance on Sunday, 2 AM - 4 AM EST.',
        description: 'The platform will be temporarily unavailable for updates.',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
        read: true,
        starred: false,
        archived: false,
        category: 'system',
        actions: [
          {
            id: 'learn-more',
            label: t('notifications:learnMore'),
            type: 'secondary',
            action: async () => { await router.push('/status') }
          }
        ],
        metadata: {
          duration: '2 hours'
        }
      },
      {
        id: '8',
        type: 'success',
        priority: 'low',
        title: t('notifications:backupCompleted'),
        message: 'Daily backup completed successfully.',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
        read: true,
        starred: false,
        archived: false,
        category: 'system',
        metadata: {
          size: '1.2 GB',
          duration: '15 minutes'
        }
      }
    ]

    setNotifications(mockNotifications)
    setIsLoading(false)
  }, [t, router, announceAction])

  // Group notifications
  useEffect(() => {
    const grouped = notifications.reduce((acc, notification) => {
      if (notification.groupId) {
        const existingGroup = acc.find(group => group.id === notification.groupId)
        if (existingGroup) {
          existingGroup.notifications.push(notification)
        } else {
          acc.push({
            id: notification.groupId,
            title: t('notifications:groupTitle', { type: notification.category }),
            notifications: [notification],
            collapsed: true
          })
        }
      }
      return acc
    }, [] as NotificationGroup[])

    setGroups(grouped)
  }, [notifications, t])

  // Filter notifications
  useEffect(() => {
    let filtered = notifications

    // Apply category filter
    if (selectedFilter !== 'all') {
      if (selectedFilter === 'unread') {
        filtered = notifications.filter(n => !n.read)
      } else if (selectedFilter === 'starred') {
        filtered = notifications.filter(n => n.starred)
      } else if (selectedFilter === 'urgent') {
        filtered = notifications.filter(n => n.priority === 'urgent')
      } else {
        filtered = notifications.filter(n => n.category === selectedFilter)
      }
    }

    // Apply archived filter
    if (!showArchived) {
      filtered = filtered.filter(n => !n.archived)
    }

    // Apply search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(n => 
        n.title.toLowerCase().includes(query) ||
        n.message.toLowerCase().includes(query) ||
        n.description?.toLowerCase().includes(query) ||
        n.sender?.name.toLowerCase().includes(query) ||
        n.target?.name.toLowerCase().includes(query)
      )
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())

    setFilteredNotifications(filtered)
  }, [notifications, selectedFilter, showArchived, searchQuery])

  // Real-time updates simulation
  useEffect(() => {
    if (!open) return

    const interval = setInterval(() => {
      // Simulate new notification
      const newNotification: Notification = {
        id: `new-${Date.now()}`,
        type: 'info',
        priority: 'low',
        title: t('notifications:newActivity'),
        message: 'Real-time notification update',
        timestamp: new Date(),
        read: false,
        starred: false,
        archived: false,
        category: 'general'
      }

      setNotifications(prev => [newNotification, ...prev])
      announceAction(t('notifications:newNotificationReceived'), 'polite')
    }, 30000) // Every 30 seconds

    return () => clearInterval(interval)
  }, [open, t, announceAction])

  const getNotificationIcon = (notification: Notification) => {
    switch (notification.type) {
      case 'success': return CheckCircle
      case 'warning': return AlertTriangle
      case 'error': return XCircle
      case 'ai': return Brain
      case 'security': return Shield
      case 'social': return Users
      case 'system': return Settings
      default: return Info
    }
  }

  const getNotificationColor = (notification: Notification) => {
    if (notification.priority === 'urgent') {
      return 'border-red-500 bg-red-50 dark:bg-red-950'
    }
    
    switch (notification.type) {
      case 'success': return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950'
      case 'warning': return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950'
      case 'error': return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950'
      case 'ai': return 'border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-950'
      case 'security': return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950'
      case 'social': return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
      case 'system': return 'border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950'
      default: return 'border-border bg-card'
    }
  }

  const getPriorityIndicator = (priority: Notification['priority']) => {
    switch (priority) {
      case 'urgent': return <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
      case 'high': return <div className="w-2 h-2 bg-orange-500 rounded-full" />
      case 'medium': return <div className="w-2 h-2 bg-yellow-500 rounded-full" />
      default: return null
    }
  }

  const handleNotificationClick = (notification: Notification) => {
    // Mark as read
    if (!notification.read) {
      setNotifications(prev => prev.map(n => 
        n.id === notification.id ? { ...n, read: true } : n
      ))
    }

    // Navigate if target exists
    if (notification.target?.href) {
      router.push(notification.target.href)
    }

    announceAction(t('notifications:notificationOpened'), 'polite')
  }

  const handleMarkAsRead = (notificationId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setNotifications(prev => prev.map(n => 
      n.id === notificationId ? { ...n, read: true } : n
    ))
    announceAction(t('notifications:markedAsRead'), 'polite')
  }

  const handleToggleStar = (notificationId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setNotifications(prev => prev.map(n => 
      n.id === notificationId ? { ...n, starred: !n.starred } : n
    ))
    announceAction(t('notifications:starToggled'), 'polite')
  }

  const handleArchive = (notificationId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setNotifications(prev => prev.map(n => 
      n.id === notificationId ? { ...n, archived: true } : n
    ))
    announceAction(t('notifications:archived'), 'polite')
  }

  const handleBulkAction = (action: 'read' | 'star' | 'archive' | 'delete') => {
    setNotifications(prev => prev.map(n => {
      if (selectedNotifications.includes(n.id)) {
        switch (action) {
          case 'read': return { ...n, read: true }
          case 'star': return { ...n, starred: !n.starred }
          case 'archive': return { ...n, archived: true }
          case 'delete': return n // Would actually remove from array
          default: return n
        }
      }
      return n
    }))

    setSelectedNotifications([])
    announceAction(t('notifications:bulkActionCompleted', { action }), 'polite')
  }

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    announceAction(t('notifications:allMarkedAsRead'), 'polite')
  }

  const filters = [
    { id: 'all', label: t('notifications:all'), icon: Bell },
    { id: 'unread', label: t('notifications:unread'), icon: BellRing },
    { id: 'starred', label: t('notifications:starred'), icon: Star },
    { id: 'urgent', label: t('notifications:urgent'), icon: AlertTriangle },
    { id: 'document', label: t('notifications:documents'), icon: FileText },
    { id: 'team', label: t('notifications:team'), icon: Users },
    { id: 'ai', label: t('notifications:ai'), icon: Brain },
    { id: 'security', label: t('notifications:security'), icon: Shield },
    { id: 'system', label: t('notifications:system'), icon: Settings }
  ]

  const unreadCount = notifications.filter(n => !n.read && !n.archived).length
  const urgentCount = notifications.filter(n => n.priority === 'urgent' && !n.read && !n.archived).length

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" dir={direction}>
      <div className="flex justify-end">
        <div
          ref={containerRef}
          className={cn(
            'w-full max-w-md h-screen bg-background border-s border-border shadow-2xl overflow-hidden',
            'animate-in slide-in-from-right duration-200',
            className
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
            <div>
              <h2 className="text-lg font-semibold">{t('notifications:notificationCenter')}</h2>
              <p className="text-sm text-muted-foreground">
                {unreadCount > 0 ? (
                  t('notifications:unreadCount', { count: unreadCount })
                ) : (
                  t('notifications:allCaughtUp')
                )}
                {urgentCount > 0 && (
                  <span className="ms-2 text-red-600">
                    • {t('notifications:urgentCount', { count: urgentCount })}
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => router.push('/settings/notifications')}
                className="p-2 rounded-lg hover:bg-muted focus-visible-ring"
                aria-label={t('notifications:settings')}
              >
                <Settings className="w-4 h-4" />
              </button>
              <button
                onClick={() => onOpenChange(false)}
                className="p-2 rounded-lg hover:bg-muted focus-visible-ring"
                aria-label={t('notifications:close')}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Controls */}
          <div className="p-4 border-b border-border space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute start-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('notifications:searchPlaceholder')}
                className="w-full ps-10 pe-4 py-2 bg-muted rounded-lg border border-border focus:border-primary focus:ring-1 focus:ring-primary focus:bg-background"
              />
            </div>

            {/* Quick actions */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    className="text-xs text-primary hover:text-primary/80 focus-visible-ring rounded"
                  >
                    {t('notifications:markAllRead')}
                  </button>
                )}
                <button
                  onClick={() => setShowArchived(!showArchived)}
                  className={cn(
                    'text-xs focus-visible-ring rounded',
                    showArchived ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {showArchived ? t('notifications:hideArchived') : t('notifications:showArchived')}
                </button>
              </div>

              {selectedNotifications.length > 0 && (
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => handleBulkAction('read')}
                    className="p-1 rounded hover:bg-muted focus-visible-ring"
                    aria-label={t('notifications:markSelectedRead')}
                  >
                    <CheckCheck className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleBulkAction('star')}
                    className="p-1 rounded hover:bg-muted focus-visible-ring"
                    aria-label={t('notifications:starSelected')}
                  >
                    <Star className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleBulkAction('archive')}
                    className="p-1 rounded hover:bg-muted focus-visible-ring"
                    aria-label={t('notifications:archiveSelected')}
                  >
                    <Archive className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleBulkAction('delete')}
                    className="p-1 rounded hover:bg-muted text-destructive focus-visible-ring"
                    aria-label={t('notifications:deleteSelected')}
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Filters */}
          <div className="flex overflow-x-auto p-2 border-b border-border">
            {filters.map((filter) => {
              const Icon = filter.icon
              const count = filter.id === 'all' ? notifications.filter(n => !n.archived).length :
                          filter.id === 'unread' ? unreadCount :
                          filter.id === 'urgent' ? urgentCount :
                          notifications.filter(n => 
                            (filter.id === 'starred' ? n.starred : n.category === filter.id) && !n.archived
                          ).length

              return (
                <button
                  key={filter.id}
                  onClick={() => setSelectedFilter(filter.id)}
                  className={cn(
                    'flex items-center space-x-2 px-3 py-2 rounded-lg border transition-colors whitespace-nowrap me-2 focus-visible-ring',
                    selectedFilter === filter.id
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-background text-muted-foreground border-border hover:bg-muted hover:text-foreground'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{filter.label}</span>
                  {count > 0 && (
                    <span className={cn(
                      'px-1.5 py-0.5 rounded-full text-xs',
                      selectedFilter === filter.id
                        ? 'bg-primary-foreground/20 text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    )}>
                      {count > 99 ? '99+' : count}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Notifications list */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-start space-x-3 p-4 rounded-lg border animate-pulse">
                    <div className="w-8 h-8 bg-muted rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-muted rounded" />
                      <div className="h-3 bg-muted rounded w-3/4" />
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredNotifications.length > 0 ? (
              <div className="p-2">
                {filteredNotifications.map((notification) => {
                  const Icon = getNotificationIcon(notification)
                  
                  return (
                    <div
                      key={notification.id}
                      className={cn(
                        'group relative mb-2 p-4 rounded-lg border transition-all cursor-pointer',
                        getNotificationColor(notification),
                        !notification.read && 'ring-2 ring-primary/20',
                        selectedNotifications.includes(notification.id) && 'ring-2 ring-primary/50 bg-primary/5'
                      )}
                      onClick={() => handleNotificationClick(notification)}
                    >
                      {/* Selection checkbox */}
                      <div className="absolute top-3 start-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <input
                          type="checkbox"
                          checked={selectedNotifications.includes(notification.id)}
                          onChange={(e) => {
                            e.stopPropagation()
                            if (e.target.checked) {
                              setSelectedNotifications(prev => [...prev, notification.id])
                            } else {
                              setSelectedNotifications(prev => prev.filter(id => id !== notification.id))
                            }
                          }}
                          className="rounded border-border focus:ring-primary"
                        />
                      </div>

                      {/* Content */}
                      <div className="flex items-start space-x-3 ms-6">
                        {/* Icon */}
                        <div className="relative">
                          <div className={cn(
                            'w-8 h-8 rounded-lg flex items-center justify-center',
                            notification.type === 'success' && 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
                            notification.type === 'warning' && 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-400',
                            notification.type === 'error' && 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
                            notification.type === 'ai' && 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
                            notification.type === 'security' && 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
                            notification.type === 'social' && 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
                            notification.type === 'system' && 'bg-gray-100 text-gray-600 dark:bg-gray-900 dark:text-gray-400',
                            notification.type === 'info' && 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
                          )}>
                            <Icon className="w-4 h-4" />
                          </div>
                          {getPriorityIndicator(notification.priority)}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-1">
                            <h3 className="text-sm font-medium line-clamp-2">
                              {notification.title}
                              {notification.badge && (
                                <span className="ms-2 px-2 py-0.5 bg-primary/20 text-primary rounded-full text-xs">
                                  {notification.badge}
                                </span>
                              )}
                            </h3>
                            
                            {/* Quick actions */}
                            <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              {!notification.read && (
                                <button
                                  onClick={(e) => handleMarkAsRead(notification.id, e)}
                                  className="p-1 rounded hover:bg-background/50 focus-visible-ring"
                                  aria-label={t('notifications:markAsRead')}
                                >
                                  <Check className="w-3 h-3" />
                                </button>
                              )}
                              <button
                                onClick={(e) => handleToggleStar(notification.id, e)}
                                className={cn(
                                  'p-1 rounded hover:bg-background/50 focus-visible-ring',
                                  notification.starred && 'text-yellow-500'
                                )}
                                aria-label={
                                  notification.starred 
                                    ? t('notifications:removeFromStarred')
                                    : t('notifications:addToStarred')
                                }
                              >
                                <Star className={cn('w-3 h-3', notification.starred && 'fill-current')} />
                              </button>
                              <button
                                onClick={(e) => handleArchive(notification.id, e)}
                                className="p-1 rounded hover:bg-background/50 focus-visible-ring"
                                aria-label={t('notifications:archive')}
                              >
                                <Archive className="w-3 h-3" />
                              </button>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                            {notification.message}
                          </p>

                          {notification.description && (
                            <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                              {notification.description}
                            </p>
                          )}

                          {/* Sender info */}
                          {notification.sender && (
                            <div className="flex items-center space-x-2 mb-2">
                              {notification.sender.avatar ? (
                                <Image
                                  src={notification.sender.avatar}
                                  alt={notification.sender.name}
                                  width={16}
                                  height={16}
                                  className="rounded-full"
                                />
                              ) : (
                                <User className="w-4 h-4 text-muted-foreground" />
                              )}
                              <span className="text-xs text-muted-foreground">
                                {notification.sender.name}
                                {notification.sender.role && ` • ${notification.sender.role}`}
                              </span>
                            </div>
                          )}

                          {/* Metadata */}
                          {notification.metadata && (
                            <div className="flex flex-wrap gap-2 mb-2">
                              {notification.metadata.size && (
                                <span className="inline-flex items-center px-2 py-1 bg-muted/50 rounded text-xs">
                                  <Database className="w-3 h-3 me-1" />
                                  {notification.metadata.size}
                                </span>
                              )}
                              {notification.metadata.duration && (
                                <span className="inline-flex items-center px-2 py-1 bg-muted/50 rounded text-xs">
                                  <Clock className="w-3 h-3 me-1" />
                                  {notification.metadata.duration}
                                </span>
                              )}
                              {notification.metadata.confidence && (
                                <span className="inline-flex items-center px-2 py-1 bg-muted/50 rounded text-xs">
                                  <Target className="w-3 h-3 me-1" />
                                  {Math.round(notification.metadata.confidence * 100)}%
                                </span>
                              )}
                              {notification.metadata.location && (
                                <span className="inline-flex items-center px-2 py-1 bg-muted/50 rounded text-xs">
                                  <MapPin className="w-3 h-3 me-1" />
                                  {notification.metadata.location}
                                </span>
                              )}
                            </div>
                          )}

                          {/* Tags */}
                          {notification.metadata?.tags && (
                            <div className="flex flex-wrap gap-1 mb-2">
                              {notification.metadata.tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="inline-flex items-center px-2 py-0.5 bg-primary/10 text-primary rounded-full text-xs"
                                >
                                  #{tag}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Actions */}
                          {notification.actions && notification.actions.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-2">
                              {notification.actions.map((action) => (
                                <button
                                  key={action.id}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    action.action()
                                  }}
                                  className={cn(
                                    'px-3 py-1 rounded text-xs font-medium transition-colors focus-visible-ring',
                                    action.type === 'primary' && 'bg-primary text-primary-foreground hover:bg-primary/90',
                                    action.type === 'secondary' && 'bg-secondary text-secondary-foreground hover:bg-secondary/90',
                                    action.type === 'destructive' && 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
                                  )}
                                >
                                  {action.label}
                                </button>
                              ))}
                            </div>
                          )}

                          {/* Timestamp */}
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <time dateTime={notification.timestamp.toISOString()}>
                              {formatDistanceToNow(notification.timestamp, { 
                                addSuffix: true,
                                locale: getDateLocale()
                              })}
                            </time>
                            {notification.target?.href && (
                              <ExternalLink className="w-3 h-3" />
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                  <Bell className="w-6 h-6 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">
                  {selectedFilter === 'all' 
                    ? t('notifications:noNotifications')
                    : t('notifications:noNotificationsForFilter')
                  }
                </h3>
                <p className="text-muted-foreground mb-4">
                  {selectedFilter === 'all' 
                    ? t('notifications:noNotificationsDescription')
                    : t('notifications:tryDifferentFilter')
                  }
                </p>
                {selectedFilter !== 'all' && (
                  <button
                    onClick={() => setSelectedFilter('all')}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 focus-visible-ring"
                  >
                    {t('notifications:showAllNotifications')}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-border bg-muted/30">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {filteredNotifications.length} {t('notifications:notificationsShown')}
              </span>
              <div className="flex items-center space-x-2">
                <Link
                  href="/settings/notifications"
                  className="text-primary hover:text-primary/80 focus-visible-ring rounded"
                >
                  {t('notifications:manageSettings')}
                </Link>
                <span>•</span>
                <button
                  onClick={() => {
                    // Clear all notifications
                    setNotifications([])
                    announceAction(t('notifications:allCleared'), 'polite')
                  }}
                  className="text-destructive hover:text-destructive/80 focus-visible-ring rounded"
                >
                  {t('notifications:clearAll')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}