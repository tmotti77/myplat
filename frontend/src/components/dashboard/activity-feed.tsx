import { useState, useEffect } from 'react'
import { useTranslation } from 'next-i18next'
import { useRouter } from 'next/router'
import { formatDistanceToNow } from 'date-fns'
import { enUS, he, ar } from 'date-fns/locale'
import Link from 'next/link'
import Image from 'next/image'
import {
  FileText,
  Upload,
  Download,
  Share2,
  MessageSquare,
  Users,
  User,
  Edit,
  Trash2,
  Star,
  Heart,
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  Eye,
  Search,
  Brain,
  Zap,
  Settings,
  Shield,
  Lock,
  Unlock,
  Key,
  Bell,
  Mail,
  Phone,
  Globe,
  MapPin,
  Calendar,
  Clock,
  Timer,
  Activity,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Target,
  Award,
  Trophy,
  Medal,
  Crown,
  Gem,
  Sparkles,
  Flame,
  Lightning,
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
  Archive,
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
  Flip,
  FlipHorizontal,
  FlipVertical,
  Maximize,
  Maximize2,
  Minimize,
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
  HardDrive as HardDriveIcon,
  Save,
  SaveAll,
  FolderOpen,
  FolderClosed,
  Trash,
  Delete,
  Backspace,
  Plus,
  Minus,
  X,
  Check,
  CheckCircle,
  XCircle,
  AlertCircle,
  AlertTriangle,
  Info,
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
  Calculator,
  Abacus,
  Ruler,
  Scissors as ScissorsIcon,
  Wrench,
  Hammer,
  Screwdriver,
  Drill,
  Saw,
  Paintbrush,
  Palette,
  Pipette,
  Eraser,
  PenTool,
  Pencil,
  Pen,
  Marker,
  Highlighter,
  Crayon,
  Brush,
  Spray,
  Bucket,
  Roller,
  Stamp,
  Sticker,
  Magnet,
  Paperclip as PaperclipIcon,
  Pin,
  Pushpin,
  Thumbtack,
  Clip,
  Stapler,
  Punch,
  Hole,
  Circle,
  Square as SquareIcon,
  Triangle,
  Pentagon,
  Hexagon,
  Octagon,
  Diamond,
  Heart as HeartIcon,
  Spade,
  Club,
  Star as StarIconTwo,
  Cross,
  Plus as PlusIcon,
  Minus as MinusIcon,
  Equal,
  NotEqual,
  GreaterThan,
  LessThan,
  GreaterThanOrEqual,
  LessThanOrEqual,
  Infinity,
  Pi,
  Sigma,
  Delta,
  Omega,
  Alpha,
  Beta,
  Gamma,
  Lambda,
  Mu,
  Nu,
  Theta,
  Phi,
  Psi,
  Chi,
  Zeta,
  Eta,
  Iota,
  Kappa,
  Omicron,
  Rho,
  Tau,
  Upsilon,
  Xi
} from '@/lib/icon-mappings'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface ActivityFeedProps {
  className?: string
  limit?: number
  showFilters?: boolean
  variant?: 'default' | 'compact' | 'detailed'
  realTime?: boolean
}

interface ActivityItem {
  id: string
  type: 'document' | 'user' | 'system' | 'ai' | 'collaboration' | 'security'
  action: 'created' | 'updated' | 'deleted' | 'viewed' | 'shared' | 'downloaded' | 'uploaded' | 'commented' | 'liked' | 'bookmarked' | 'searched' | 'processed' | 'joined' | 'left' | 'invited' | 'promoted' | 'demoted' | 'logged_in' | 'logged_out' | 'backup' | 'restore' | 'maintenance'
  title: string
  description: string
  timestamp: Date
  user?: {
    id: string
    name: string
    avatar?: string
    role?: string
  }
  target?: {
    id: string
    name: string
    type: 'document' | 'collection' | 'user' | 'system'
    href?: string
  }
  metadata?: {
    size?: string
    duration?: string
    confidence?: number
    tags?: string[]
    location?: string
    device?: string
    ip?: string
  }
  severity?: 'low' | 'medium' | 'high' | 'critical'
  category?: string
  isNew?: boolean
}

export function ActivityFeed({
  className,
  limit = 10,
  showFilters = true,
  variant = 'default',
  realTime = true
}: ActivityFeedProps) {
  const { t } = useTranslation(['dashboard', 'common'])
  const router = useRouter()
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [filteredActivities, setFilteredActivities] = useState<ActivityItem[]>([])
  const [selectedFilter, setSelectedFilter] = useState<string>('all')
  const [isLoading, setIsLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)

  // Get appropriate locale for date formatting
  const getDateLocale = () => {
    switch (router.locale) {
      case 'he': return he
      case 'ar': return ar
      default: return enUS
    }
  }

  // Mock activity data - replace with actual API calls
  useEffect(() => {
    const mockActivities: ActivityItem[] = [
      {
        id: '1',
        type: 'document',
        action: 'uploaded',
        title: t('dashboard:activityDocumentUploaded'),
        description: 'Annual Report 2024.pdf',
        timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        user: {
          id: 'user-1',
          name: 'Sarah Johnson',
          avatar: '/avatars/sarah.jpg',
          role: 'Product Manager'
        },
        target: {
          id: 'doc-1',
          name: 'Annual Report 2024.pdf',
          type: 'document',
          href: '/documents/annual-report-2024'
        },
        metadata: {
          size: '2.4 MB',
          tags: ['report', 'annual', '2024']
        },
        isNew: true
      },
      {
        id: '2',
        type: 'ai',
        action: 'processed',
        title: t('dashboard:activityAIProcessed'),
        description: 'AI analysis completed with 95% confidence',
        timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
        target: {
          id: 'analysis-1',
          name: 'Market Research Q4',
          type: 'document',
          href: '/documents/market-research-q4'
        },
        metadata: {
          confidence: 0.95,
          duration: '2.3s'
        },
        isNew: true
      },
      {
        id: '3',
        type: 'collaboration',
        action: 'commented',
        title: t('dashboard:activityCommented'),
        description: 'Added feedback on product roadmap',
        timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
        user: {
          id: 'user-2',
          name: 'Mike Chen',
          avatar: '/avatars/mike.jpg',
          role: 'Developer'
        },
        target: {
          id: 'doc-2',
          name: 'Product Roadmap',
          type: 'document',
          href: '/documents/product-roadmap'
        }
      },
      {
        id: '4',
        type: 'user',
        action: 'joined',
        title: t('dashboard:activityUserJoined'),
        description: 'New team member joined the workspace',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        user: {
          id: 'user-3',
          name: 'Emma Wilson',
          avatar: '/avatars/emma.jpg',
          role: 'Designer'
        },
        metadata: {
          location: 'San Francisco, CA'
        }
      },
      {
        id: '5',
        type: 'document',
        action: 'shared',
        title: t('dashboard:activityDocumentShared'),
        description: 'Shared with 3 team members',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
        user: {
          id: 'user-4',
          name: 'David Kim',
          avatar: '/avatars/david.jpg',
          role: 'Manager'
        },
        target: {
          id: 'doc-3',
          name: 'Design Guidelines',
          type: 'document',
          href: '/documents/design-guidelines'
        }
      },
      {
        id: '6',
        type: 'system',
        action: 'backup',
        title: t('dashboard:activitySystemBackup'),
        description: 'Automated backup completed successfully',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
        metadata: {
          size: '1.2 GB',
          duration: '15 minutes'
        },
        severity: 'low'
      },
      {
        id: '7',
        type: 'document',
        action: 'viewed',
        title: t('dashboard:activityDocumentViewed'),
        description: 'Document accessed from mobile device',
        timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000), // 8 hours ago
        user: {
          id: 'user-5',
          name: 'Lisa Anderson',
          avatar: '/avatars/lisa.jpg',
          role: 'Analyst'
        },
        target: {
          id: 'doc-4',
          name: 'Financial Report Q3',
          type: 'document',
          href: '/documents/financial-report-q3'
        },
        metadata: {
          device: 'iPhone 15 Pro',
          location: 'New York, NY'
        }
      },
      {
        id: '8',
        type: 'security',
        action: 'logged_in',
        title: t('dashboard:activitySecurityLogin'),
        description: 'Login from new device detected',
        timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000), // 12 hours ago
        user: {
          id: 'user-6',
          name: 'John Smith',
          avatar: '/avatars/john.jpg',
          role: 'Admin'
        },
        metadata: {
          device: 'MacBook Pro',
          location: 'London, UK',
          ip: '192.168.1.100'
        },
        severity: 'medium'
      },
      {
        id: '9',
        type: 'ai',
        action: 'searched',
        title: t('dashboard:activityAISearch'),
        description: 'AI-powered search query processed',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
        user: {
          id: 'user-7',
          name: 'Alex Turner',
          avatar: '/avatars/alex.jpg',
          role: 'Researcher'
        },
        metadata: {
          confidence: 0.88,
          duration: '1.1s'
        }
      },
      {
        id: '10',
        type: 'collaboration',
        action: 'shared',
        title: t('dashboard:activityCollectionShared'),
        description: 'Marketing materials collection shared externally',
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
        user: {
          id: 'user-8',
          name: 'Rachel Green',
          avatar: '/avatars/rachel.jpg',
          role: 'Marketing'
        },
        target: {
          id: 'collection-1',
          name: 'Marketing Materials',
          type: 'collection',
          href: '/collections/marketing-materials'
        }
      }
    ]

    setActivities(mockActivities)
    setIsLoading(false)
  }, [t])

  // Filter activities
  useEffect(() => {
    let filtered = activities

    if (selectedFilter !== 'all') {
      filtered = activities.filter(activity => activity.type === selectedFilter)
    }

    if (!showAll) {
      filtered = filtered.slice(0, limit)
    }

    setFilteredActivities(filtered)
  }, [activities, selectedFilter, showAll, limit])

  // Real-time updates simulation
  useEffect(() => {
    if (!realTime) return

    const interval = setInterval(() => {
      // Simulate new activity
      const newActivity: ActivityItem = {
        id: `new-${Date.now()}`,
        type: 'document',
        action: 'viewed',
        title: t('dashboard:activityDocumentViewed'),
        description: 'Real-time activity update',
        timestamp: new Date(),
        user: {
          id: 'user-current',
          name: 'Current User',
          role: 'User'
        },
        isNew: true
      }

      setActivities(prev => [newActivity, ...prev])
      
      // Announce new activity for screen readers
      announceAction(t('dashboard:newActivityAnnouncement'), 'polite')
    }, 30000) // Every 30 seconds

    return () => clearInterval(interval)
  }, [realTime, announceAction, t])

  const getActivityIcon = (activity: ActivityItem) => {
    switch (activity.type) {
      case 'document':
        switch (activity.action) {
          case 'uploaded': return Upload
          case 'downloaded': return Download
          case 'shared': return Share2
          case 'viewed': return Eye
          case 'updated': return Edit
          case 'deleted': return Trash2
          case 'bookmarked': return Bookmark
          default: return FileText
        }
      case 'user':
        switch (activity.action) {
          case 'joined': return User
          case 'left': return ArrowLeft
          case 'invited': return Mail
          case 'promoted': return TrendingUp
          case 'demoted': return TrendingDown
          case 'logged_in': return LogIn
          case 'logged_out': return LogOut
          default: return Users
        }
      case 'ai':
        switch (activity.action) {
          case 'processed': return Brain
          case 'searched': return Search
          default: return Sparkles
        }
      case 'collaboration':
        switch (activity.action) {
          case 'commented': return MessageSquare
          case 'shared': return Share2
          case 'liked': return Heart
          default: return Users
        }
      case 'security':
        switch (activity.action) {
          case 'logged_in': return Shield
          case 'logged_out': return Lock
          default: return Key
        }
      case 'system':
        switch (activity.action) {
          case 'backup': return Archive
          case 'restore': return RotateCcw
          case 'maintenance': return Settings
          default: return Server
        }
      default:
        return Activity
    }
  }

  const getActivityColor = (activity: ActivityItem) => {
    if (activity.isNew) {
      return 'text-primary bg-primary/10'
    }

    switch (activity.type) {
      case 'document': return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900'
      case 'user': return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900'
      case 'ai': return 'text-purple-600 bg-purple-100 dark:text-purple-400 dark:bg-purple-900'
      case 'collaboration': return 'text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900'
      case 'security': return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900'
      case 'system': return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getSeverityColor = (severity?: ActivityItem['severity']) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50 dark:bg-red-950'
      case 'high': return 'border-orange-500 bg-orange-50 dark:bg-orange-950'
      case 'medium': return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950'
      case 'low': return 'border-blue-500 bg-blue-50 dark:bg-blue-950'
      default: return ''
    }
  }

  const filters = [
    { id: 'all', label: t('dashboard:allActivities'), icon: Activity },
    { id: 'document', label: t('dashboard:documents'), icon: FileText },
    { id: 'user', label: t('dashboard:users'), icon: Users },
    { id: 'ai', label: t('dashboard:aiActivities'), icon: Brain },
    { id: 'collaboration', label: t('dashboard:collaboration'), icon: Share2 },
    { id: 'security', label: t('dashboard:security'), icon: Shield },
    { id: 'system', label: t('dashboard:system'), icon: Server }
  ]

  const handleActivityClick = (activity: ActivityItem) => {
    if (activity.target?.href) {
      router.push(activity.target.href)
      announceAction(t('dashboard:navigatingToActivity'), 'polite')
    }
  }

  if (variant === 'compact') {
    return (
      <div className={cn('space-y-3', className)} dir={direction}>
        {filteredActivities.slice(0, 5).map((activity) => {
          const Icon = getActivityIcon(activity)
          return (
            <div
              key={activity.id}
              className={cn(
                'flex items-center space-x-3 p-3 rounded-lg border transition-colors',
                activity.target?.href && 'hover:bg-muted cursor-pointer',
                getSeverityColor(activity.severity)
              )}
              onClick={() => handleActivityClick(activity)}
            >
              <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center', getActivityColor(activity))}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{activity.title}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDistanceToNow(activity.timestamp, { 
                    addSuffix: true,
                    locale: getDateLocale()
                  })}
                </p>
              </div>
              {activity.isNew && (
                <div className="w-2 h-2 bg-primary rounded-full" />
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)} dir={direction}>
      {/* Filters */}
      {showFilters && (
        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => {
            const Icon = filter.icon
            return (
              <button
                key={filter.id}
                onClick={() => setSelectedFilter(filter.id)}
                className={cn(
                  'flex items-center space-x-2 px-3 py-2 rounded-lg border transition-colors focus-visible-ring',
                  selectedFilter === filter.id
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background text-muted-foreground border-border hover:bg-muted hover:text-foreground'
                )}
                aria-pressed={selectedFilter === filter.id}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{filter.label}</span>
              </button>
            )
          })}
        </div>
      )}

      {/* Activity list */}
      <div className="space-y-1">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center space-x-3 p-4 rounded-lg border">
                <div className="w-10 h-10 bg-muted rounded-lg animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded animate-pulse" />
                  <div className="h-3 bg-muted rounded w-1/2 animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredActivities.length > 0 ? (
          filteredActivities.map((activity, index) => {
            const Icon = getActivityIcon(activity)
            
            return (
              <div
                key={activity.id}
                className={cn(
                  'group relative flex items-start space-x-4 p-4 rounded-lg border transition-all',
                  activity.target?.href && 'hover:bg-muted cursor-pointer hover:shadow-sm',
                  getSeverityColor(activity.severity),
                  activity.isNew && 'ring-2 ring-primary/20'
                )}
                onClick={() => handleActivityClick(activity)}
              >
                {/* Timeline line */}
                {index < filteredActivities.length - 1 && (
                  <div className="absolute start-6 top-14 w-px h-12 bg-border" />
                )}

                {/* Activity icon */}
                <div className={cn('relative w-10 h-10 rounded-lg flex items-center justify-center', getActivityColor(activity))}>
                  <Icon className="w-5 h-5" />
                  {activity.isNew && (
                    <div className="absolute -top-1 -end-1 w-3 h-3 bg-primary rounded-full border-2 border-background" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground">
                        {activity.title}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {activity.description}
                      </p>
                      
                      {/* User info */}
                      {activity.user && (
                        <div className="flex items-center space-x-2 mt-2">
                          {activity.user.avatar ? (
                            <Image
                              src={activity.user.avatar}
                              alt={activity.user.name}
                              width={20}
                              height={20}
                              className="rounded-full"
                            />
                          ) : (
                            <div className="w-5 h-5 bg-primary/20 rounded-full flex items-center justify-center">
                              <User className="w-3 h-3 text-primary" />
                            </div>
                          )}
                          <span className="text-xs text-muted-foreground">
                            {activity.user.name}
                            {activity.user.role && ` • ${activity.user.role}`}
                          </span>
                        </div>
                      )}

                      {/* Metadata */}
                      {activity.metadata && variant === 'detailed' && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {activity.metadata.size && (
                            <span className="inline-flex items-center px-2 py-1 bg-muted rounded text-xs">
                              <Database className="w-3 h-3 me-1" />
                              {activity.metadata.size}
                            </span>
                          )}
                          {activity.metadata.duration && (
                            <span className="inline-flex items-center px-2 py-1 bg-muted rounded text-xs">
                              <Clock className="w-3 h-3 me-1" />
                              {activity.metadata.duration}
                            </span>
                          )}
                          {activity.metadata.confidence && (
                            <span className="inline-flex items-center px-2 py-1 bg-muted rounded text-xs">
                              <Target className="w-3 h-3 me-1" />
                              {Math.round(activity.metadata.confidence * 100)}%
                            </span>
                          )}
                          {activity.metadata.location && (
                            <span className="inline-flex items-center px-2 py-1 bg-muted rounded text-xs">
                              <MapPin className="w-3 h-3 me-1" />
                              {activity.metadata.location}
                            </span>
                          )}
                          {activity.metadata.device && (
                            <span className="inline-flex items-center px-2 py-1 bg-muted rounded text-xs">
                              <Smartphone className="w-3 h-3 me-1" />
                              {activity.metadata.device}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Tags */}
                      {activity.metadata?.tags && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {activity.metadata.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center px-2 py-0.5 bg-primary/10 text-primary rounded-full text-xs"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Timestamp */}
                    <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                      <time dateTime={activity.timestamp.toISOString()}>
                        {formatDistanceToNow(activity.timestamp, { 
                          addSuffix: true,
                          locale: getDateLocale()
                        })}
                      </time>
                      {activity.target?.href && (
                        <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        ) : (
          <div className="text-center py-8">
            <div className="w-12 h-12 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <Activity className="w-5 h-5 text-muted-foreground" />
            </div>
            <h3 className="text-sm font-medium mb-1">
              {t('dashboard:noActivitiesFound')}
            </h3>
            <p className="text-xs text-muted-foreground">
              {t('dashboard:noActivitiesDescription')}
            </p>
          </div>
        )}
      </div>

      {/* Show more button */}
      {!showAll && activities.length > limit && (
        <button
          onClick={() => setShowAll(true)}
          className="w-full py-2 text-sm text-primary hover:text-primary/80 focus-visible-ring rounded"
        >
          {t('dashboard:showMoreActivities', { count: activities.length - limit })}
        </button>
      )}

      {/* Real-time indicator */}
      {realTime && (
        <div className="flex items-center justify-center space-x-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span>{t('dashboard:realTimeUpdates')}</span>
        </div>
      )}
    </div>
  )
}

// Helper components that were referenced but need to be defined
function LogIn({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
    </svg>
  )
}

function LogOut({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  )
}