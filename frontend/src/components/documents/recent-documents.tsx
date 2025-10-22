import { useState, useEffect } from 'react'
import { useTranslation } from 'next-i18next'
import { useRouter } from 'next/router'
import { formatDistanceToNow } from 'date-fns'
import { enUS, he, ar } from 'date-fns/locale'
import Link from 'next/link'
import Image from 'next/image'
import {
  FileText,
  File,
  FileImage,
  FileVideo,
  FileAudio,
  FileSpreadsheet,
  FileBarChart,
  FilePlus,
  Eye,
  Download,
  Share2,
  Star,
  Heart,
  Bookmark,
  Edit,
  Trash2,
  Copy,
  MoreHorizontal,
  Clock,
  Calendar,
  User,
  Users,
  Tag,
  Filter,
  Search,
  SlidersHorizontal,
  Grid3X3,
  List,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Award,
  Trophy,
  Medal,
  Crown,
  Sparkles,
  Zap,
  Brain,
  Target,
  Activity,
  Database,
  Server,
  Cloud,
  Shield,
  Lock,
  Unlock,
  Key,
  Settings,
  HelpCircle,
  Info,
  AlertCircle,
  CheckCircle,
  XCircle,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ExternalLink,
  Maximize2,
  Minimize2,
  RotateCcw,
  RefreshCw,
  Plus,
  Minus,
  X,
  Check,
  Upload,
  FolderPlus,
  Folder,
  FolderOpen,
  Archive,
  Trash,
  Save,
  SaveAll,
  Pin,
  Paperclip,
  Link as LinkIcon,
  Globe,
  Mail,
  Phone,
  MapPin,
  Navigation,
  Compass,
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
  CloudRain,
  Umbrella,
  Wind,
  Thermometer,
  Droplets,
  Waves,
  Cpu,
  HardDrive,
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
  Package
} from 'lucide-react'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface RecentDocumentsProps {
  className?: string
  limit?: number
  showFilters?: boolean
  variant?: 'default' | 'compact' | 'grid' | 'list'
  showActions?: boolean
}

interface Document {
  id: string
  title: string
  description?: string
  type: 'pdf' | 'doc' | 'ppt' | 'xlsx' | 'txt' | 'image' | 'video' | 'audio' | 'other'
  size: string
  lastModified: Date
  lastAccessed?: Date
  author: {
    id: string
    name: string
    avatar?: string
    role?: string
  }
  tags: string[]
  isStarred: boolean
  isBookmarked: boolean
  shareCount: number
  viewCount: number
  downloadCount: number
  confidence?: number
  aiSummary?: string
  thumbnail?: string
  href: string
  status: 'processing' | 'ready' | 'error' | 'archived'
  permissions: {
    canView: boolean
    canEdit: boolean
    canShare: boolean
    canDelete: boolean
  }
  metadata?: {
    pages?: number
    duration?: string
    resolution?: string
    language?: string
    extractedText?: string
  }
  relatedDocuments?: string[]
  collaborators?: Array<{
    id: string
    name: string
    avatar?: string
    role: 'viewer' | 'editor' | 'owner'
  }>
}

export function RecentDocuments({
  className,
  limit = 10,
  showFilters = true,
  variant = 'default',
  showActions = true
}: RecentDocumentsProps) {
  const { t } = useTranslation(['documents', 'common'])
  const router = useRouter()
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [documents, setDocuments] = useState<Document[]>([])
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([])
  const [selectedFilter, setSelectedFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'recent' | 'name' | 'size' | 'author'>('recent')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(variant === 'grid' ? 'grid' : 'list')
  const [isLoading, setIsLoading] = useState(true)
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([])
  const [showBulkActions, setShowBulkActions] = useState(false)

  // Get appropriate locale for date formatting
  const getDateLocale = () => {
    switch (router.locale) {
      case 'he': return he
      case 'ar': return ar
      default: return enUS
    }
  }

  // Mock documents data - replace with actual API calls
  useEffect(() => {
    const mockDocuments: Document[] = [
      {
        id: '1',
        title: 'Annual Report 2024.pdf',
        description: 'Comprehensive annual report with financial statements and market analysis',
        type: 'pdf',
        size: '2.4 MB',
        lastModified: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        lastAccessed: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
        author: {
          id: 'user-1',
          name: 'Sarah Johnson',
          avatar: '/avatars/sarah.jpg',
          role: 'Product Manager'
        },
        tags: ['report', 'annual', '2024', 'financial'],
        isStarred: true,
        isBookmarked: false,
        shareCount: 12,
        viewCount: 45,
        downloadCount: 8,
        confidence: 0.95,
        aiSummary: 'This document contains financial performance data and strategic objectives for 2024.',
        thumbnail: '/thumbnails/annual-report.jpg',
        href: '/documents/annual-report-2024',
        status: 'ready',
        permissions: {
          canView: true,
          canEdit: true,
          canShare: true,
          canDelete: true
        },
        metadata: {
          pages: 84,
          language: 'English'
        },
        collaborators: [
          { id: 'user-2', name: 'Mike Chen', avatar: '/avatars/mike.jpg', role: 'editor' },
          { id: 'user-3', name: 'Emma Wilson', role: 'viewer' }
        ]
      },
      {
        id: '2',
        title: 'Product Roadmap Q1-Q2.pptx',
        description: 'Strategic product roadmap presentation for the first two quarters',
        type: 'ppt',
        size: '8.7 MB',
        lastModified: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        author: {
          id: 'user-2',
          name: 'Mike Chen',
          avatar: '/avatars/mike.jpg',
          role: 'Developer'
        },
        tags: ['roadmap', 'product', 'strategy', 'q1', 'q2'],
        isStarred: false,
        isBookmarked: true,
        shareCount: 8,
        viewCount: 23,
        downloadCount: 5,
        confidence: 0.88,
        thumbnail: '/thumbnails/roadmap.jpg',
        href: '/documents/product-roadmap-q1-q2',
        status: 'ready',
        permissions: {
          canView: true,
          canEdit: false,
          canShare: true,
          canDelete: false
        },
        metadata: {
          pages: 32,
          language: 'English'
        }
      },
      {
        id: '3',
        title: 'Market Research Data.xlsx',
        description: 'Comprehensive market analysis with customer segmentation data',
        type: 'xlsx',
        size: '1.2 MB',
        lastModified: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
        author: {
          id: 'user-3',
          name: 'Emma Wilson',
          avatar: '/avatars/emma.jpg',
          role: 'Designer'
        },
        tags: ['market', 'research', 'data', 'analysis'],
        isStarred: false,
        isBookmarked: false,
        shareCount: 15,
        viewCount: 67,
        downloadCount: 12,
        confidence: 0.92,
        href: '/documents/market-research-data',
        status: 'ready',
        permissions: {
          canView: true,
          canEdit: true,
          canShare: true,
          canDelete: false
        },
        metadata: {
          language: 'English'
        }
      },
      {
        id: '4',
        title: 'Team Meeting Recording.mp4',
        description: 'Weekly team sync meeting recording with action items',
        type: 'video',
        size: '156 MB',
        lastModified: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
        author: {
          id: 'user-4',
          name: 'David Kim',
          avatar: '/avatars/david.jpg',
          role: 'Manager'
        },
        tags: ['meeting', 'team', 'sync', 'recording'],
        isStarred: false,
        isBookmarked: false,
        shareCount: 6,
        viewCount: 18,
        downloadCount: 3,
        href: '/documents/team-meeting-recording',
        status: 'processing',
        permissions: {
          canView: true,
          canEdit: false,
          canShare: false,
          canDelete: false
        },
        metadata: {
          duration: '45:32',
          resolution: '1920x1080'
        }
      },
      {
        id: '5',
        title: 'Design Guidelines.pdf',
        description: 'Updated brand and design system guidelines for 2024',
        type: 'pdf',
        size: '5.1 MB',
        lastModified: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
        author: {
          id: 'user-5',
          name: 'Lisa Anderson',
          avatar: '/avatars/lisa.jpg',
          role: 'Analyst'
        },
        tags: ['design', 'guidelines', 'brand', 'system'],
        isStarred: true,
        isBookmarked: true,
        shareCount: 22,
        viewCount: 89,
        downloadCount: 18,
        confidence: 0.97,
        thumbnail: '/thumbnails/design-guidelines.jpg',
        href: '/documents/design-guidelines',
        status: 'ready',
        permissions: {
          canView: true,
          canEdit: false,
          canShare: true,
          canDelete: false
        },
        metadata: {
          pages: 156,
          language: 'English'
        }
      }
    ]

    setDocuments(mockDocuments)
    setIsLoading(false)
  }, [])

  // Filter and sort documents
  useEffect(() => {
    let filtered = documents

    // Apply type filter
    if (selectedFilter !== 'all') {
      if (selectedFilter === 'starred') {
        filtered = documents.filter(doc => doc.isStarred)
      } else if (selectedFilter === 'bookmarked') {
        filtered = documents.filter(doc => doc.isBookmarked)
      } else if (selectedFilter === 'shared') {
        filtered = documents.filter(doc => doc.shareCount > 0)
      } else {
        filtered = documents.filter(doc => doc.type === selectedFilter)
      }
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.title.localeCompare(b.title)
        case 'size':
          return parseFloat(a.size) - parseFloat(b.size)
        case 'author':
          return a.author.name.localeCompare(b.author.name)
        case 'recent':
        default:
          return b.lastModified.getTime() - a.lastModified.getTime()
      }
    })

    setFilteredDocuments(filtered.slice(0, limit))
  }, [documents, selectedFilter, sortBy, limit])

  const getDocumentIcon = (type: Document['type']) => {
    switch (type) {
      case 'pdf': return FileText
      case 'doc': return FileText
      case 'ppt': return FileText
      case 'xlsx': return FileSpreadsheet
      case 'txt': return File
      case 'image': return FileImage
      case 'video': return FileVideo
      case 'audio': return FileAudio
      default: return File
    }
  }

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'ready': return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900'
      case 'processing': return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900'
      case 'error': return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900'
      case 'archived': return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900'
    }
  }

  const formatFileSize = (size: string) => {
    const numSize = parseFloat(size)
    const unit = size.replace(numSize.toString(), '').trim()
    return `${numSize.toFixed(1)} ${unit}`
  }

  const handleDocumentClick = (document: Document) => {
    router.push(document.href)
    announceAction(t('documents:navigatingToDocument', { title: document.title }), 'polite')
  }

  const handleStarToggle = (documentId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setDocuments(prev => prev.map(doc => 
      doc.id === documentId ? { ...doc, isStarred: !doc.isStarred } : doc
    ))
    announceAction(t('documents:starToggled'), 'polite')
  }

  const handleBookmarkToggle = (documentId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setDocuments(prev => prev.map(doc => 
      doc.id === documentId ? { ...doc, isBookmarked: !doc.isBookmarked } : doc
    ))
    announceAction(t('documents:bookmarkToggled'), 'polite')
  }

  const handleBulkAction = (action: 'star' | 'bookmark' | 'share' | 'delete') => {
    // Handle bulk actions
    setSelectedDocuments([])
    setShowBulkActions(false)
    announceAction(t('documents:bulkActionCompleted', { action }), 'polite')
  }

  const filters = [
    { id: 'all', label: t('documents:allDocuments'), icon: FileText },
    { id: 'pdf', label: 'PDF', icon: FileText },
    { id: 'doc', label: 'Word', icon: FileText },
    { id: 'ppt', label: 'PowerPoint', icon: FileText },
    { id: 'xlsx', label: 'Excel', icon: FileSpreadsheet },
    { id: 'image', label: t('documents:images'), icon: FileImage },
    { id: 'video', label: t('documents:videos'), icon: FileVideo },
    { id: 'starred', label: t('documents:starred'), icon: Star },
    { id: 'bookmarked', label: t('documents:bookmarked'), icon: Bookmark },
    { id: 'shared', label: t('documents:shared'), icon: Share2 }
  ]

  const sortOptions = [
    { id: 'recent', label: t('documents:mostRecent') },
    { id: 'name', label: t('documents:name') },
    { id: 'size', label: t('documents:size') },
    { id: 'author', label: t('documents:author') }
  ]

  if (variant === 'compact') {
    return (
      <div className={cn('space-y-3', className)} dir={direction}>
        {filteredDocuments.slice(0, 5).map((document) => {
          const Icon = getDocumentIcon(document.type)
          return (
            <div
              key={document.id}
              className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-muted cursor-pointer transition-colors"
              onClick={() => handleDocumentClick(document)}
            >
              <div className="w-8 h-8 bg-muted rounded-lg flex items-center justify-center">
                <Icon className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{document.title}</p>
                <p className="text-xs text-muted-foreground">
                  {document.size} • {formatDistanceToNow(document.lastModified, { 
                    addSuffix: true,
                    locale: getDateLocale()
                  })}
                </p>
              </div>
              {document.isStarred && (
                <Star className="w-4 h-4 text-yellow-500 fill-current" />
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)} dir={direction}>
      {/* Controls */}
      {showFilters && (
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-4 lg:space-y-0">
          {/* Filters */}
          <div className="flex flex-wrap gap-2">
            {filters.slice(0, 6).map((filter) => {
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

          {/* Sort and view controls */}
          <div className="flex items-center space-x-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="px-3 py-2 text-sm bg-background border border-border rounded-lg focus:border-primary focus:ring-1 focus:ring-primary"
            >
              {sortOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>

            <div className="flex rounded-lg border border-border">
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'p-2 rounded-s-lg focus-visible-ring',
                  viewMode === 'list' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                )}
                aria-label={t('documents:listView')}
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'p-2 rounded-e-lg focus-visible-ring',
                  viewMode === 'grid' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                )}
                aria-label={t('documents:gridView')}
              >
                <Grid3X3 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk actions */}
      {selectedDocuments.length > 0 && (
        <div className="flex items-center justify-between p-3 bg-primary/10 rounded-lg border border-primary/20">
          <span className="text-sm font-medium">
            {t('documents:selectedCount', { count: selectedDocuments.length })}
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleBulkAction('star')}
              className="p-2 rounded-lg hover:bg-background focus-visible-ring"
              aria-label={t('documents:starSelected')}
            >
              <Star className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleBulkAction('bookmark')}
              className="p-2 rounded-lg hover:bg-background focus-visible-ring"
              aria-label={t('documents:bookmarkSelected')}
            >
              <Bookmark className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleBulkAction('share')}
              className="p-2 rounded-lg hover:bg-background focus-visible-ring"
              aria-label={t('documents:shareSelected')}
            >
              <Share2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleBulkAction('delete')}
              className="p-2 rounded-lg hover:bg-background text-destructive focus-visible-ring"
              aria-label={t('documents:deleteSelected')}
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setSelectedDocuments([])}
              className="p-2 rounded-lg hover:bg-background focus-visible-ring"
              aria-label={t('documents:clearSelection')}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Documents grid/list */}
      {isLoading ? (
        <div className={cn(
          'grid gap-4',
          viewMode === 'grid' 
            ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
            : 'grid-cols-1'
        )}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="p-4 rounded-lg border animate-pulse">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 bg-muted rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded" />
                  <div className="h-3 bg-muted rounded w-1/2" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 bg-muted rounded" />
                <div className="h-3 bg-muted rounded w-3/4" />
              </div>
            </div>
          ))}
        </div>
      ) : filteredDocuments.length > 0 ? (
        <div className={cn(
          'grid gap-4',
          viewMode === 'grid' 
            ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
            : 'grid-cols-1'
        )}>
          {filteredDocuments.map((document) => {
            const Icon = getDocumentIcon(document.type)
            
            return (
              <div
                key={document.id}
                className={cn(
                  'group relative p-4 rounded-lg border transition-all duration-200 hover:shadow-md cursor-pointer',
                  viewMode === 'list' && 'flex items-center space-x-4',
                  document.status === 'processing' && 'opacity-75',
                  selectedDocuments.includes(document.id) && 'ring-2 ring-primary/20 bg-primary/5'
                )}
                onClick={() => handleDocumentClick(document)}
              >
                {/* Selection checkbox */}
                {showActions && (
                  <div className="absolute top-3 start-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <input
                      type="checkbox"
                      checked={selectedDocuments.includes(document.id)}
                      onChange={(e) => {
                        e.stopPropagation()
                        if (e.target.checked) {
                          setSelectedDocuments(prev => [...prev, document.id])
                        } else {
                          setSelectedDocuments(prev => prev.filter(id => id !== document.id))
                        }
                      }}
                      className="rounded border-border focus:ring-primary"
                    />
                  </div>
                )}

                {/* Document content */}
                <div className={cn(
                  'flex items-start space-x-3',
                  viewMode === 'grid' && 'flex-col space-x-0 space-y-3'
                )}>
                  {/* Icon/Thumbnail */}
                  <div className={cn(
                    'relative flex-shrink-0',
                    viewMode === 'grid' && 'w-full'
                  )}>
                    {document.thumbnail ? (
                      <div className={cn(
                        'relative overflow-hidden rounded-lg bg-muted',
                        viewMode === 'grid' ? 'aspect-[4/3] w-full' : 'w-12 h-12'
                      )}>
                        <Image
                          src={document.thumbnail}
                          alt={document.title}
                          fill
                          className="object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
                      </div>
                    ) : (
                      <div className={cn(
                        'bg-muted rounded-lg flex items-center justify-center',
                        viewMode === 'grid' ? 'aspect-[4/3] w-full' : 'w-12 h-12'
                      )}>
                        <Icon className={cn(
                          'text-muted-foreground',
                          viewMode === 'grid' ? 'w-8 h-8' : 'w-6 h-6'
                        )} />
                      </div>
                    )}

                    {/* Status indicator */}
                    {document.status !== 'ready' && (
                      <div className={cn(
                        'absolute top-2 end-2 px-2 py-1 rounded-full text-xs font-medium',
                        getStatusColor(document.status)
                      )}>
                        {t(`documents:status${document.status.charAt(0).toUpperCase() + document.status.slice(1)}`)}
                      </div>
                    )}
                  </div>

                  {/* Document info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-sm font-medium line-clamp-2">
                        {document.title}
                      </h3>
                      
                      {/* Quick actions */}
                      {showActions && (
                        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => handleStarToggle(document.id, e)}
                            className={cn(
                              'p-1 rounded hover:bg-muted focus-visible-ring',
                              document.isStarred && 'text-yellow-500'
                            )}
                            aria-label={
                              document.isStarred 
                                ? t('documents:removeFromStarred')
                                : t('documents:addToStarred')
                            }
                          >
                            <Star className={cn('w-4 h-4', document.isStarred && 'fill-current')} />
                          </button>
                          <button
                            onClick={(e) => handleBookmarkToggle(document.id, e)}
                            className={cn(
                              'p-1 rounded hover:bg-muted focus-visible-ring',
                              document.isBookmarked && 'text-primary'
                            )}
                            aria-label={
                              document.isBookmarked 
                                ? t('documents:removeFromBookmarks')
                                : t('documents:addToBookmarks')
                            }
                          >
                            <Bookmark className={cn('w-4 h-4', document.isBookmarked && 'fill-current')} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              // Show more actions menu
                            }}
                            className="p-1 rounded hover:bg-muted focus-visible-ring"
                            aria-label={t('documents:moreActions')}
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>

                    {document.description && viewMode === 'grid' && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                        {document.description}
                      </p>
                    )}

                    {/* AI Summary */}
                    {document.aiSummary && viewMode === 'grid' && (
                      <div className="flex items-start space-x-2 mb-2 p-2 bg-muted/50 rounded">
                        <Brain className="w-3 h-3 text-primary mt-0.5 flex-shrink-0" />
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {document.aiSummary}
                        </p>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                      <div className="flex items-center space-x-2">
                        <span>{formatFileSize(document.size)}</span>
                        {document.metadata?.pages && (
                          <>
                            <span>•</span>
                            <span>{t('documents:pages', { count: document.metadata.pages })}</span>
                          </>
                        )}
                        {document.metadata?.duration && (
                          <>
                            <span>•</span>
                            <span>{document.metadata.duration}</span>
                          </>
                        )}
                      </div>
                      {document.confidence && (
                        <div className="flex items-center space-x-1">
                          <Target className="w-3 h-3" />
                          <span>{Math.round(document.confidence * 100)}%</span>
                        </div>
                      )}
                    </div>

                    {/* Author and date */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {document.author.avatar ? (
                          <Image
                            src={document.author.avatar}
                            alt={document.author.name}
                            width={16}
                            height={16}
                            className="rounded-full"
                          />
                        ) : (
                          <User className="w-4 h-4 text-muted-foreground" />
                        )}
                        <span className="text-xs text-muted-foreground">
                          {document.author.name}
                        </span>
                      </div>
                      <time
                        dateTime={document.lastModified.toISOString()}
                        className="text-xs text-muted-foreground"
                      >
                        {formatDistanceToNow(document.lastModified, { 
                          addSuffix: true,
                          locale: getDateLocale()
                        })}
                      </time>
                    </div>

                    {/* Tags */}
                    {document.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {document.tags.slice(0, viewMode === 'grid' ? 3 : 5).map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-2 py-0.5 bg-primary/10 text-primary rounded-full text-xs"
                          >
                            #{tag}
                          </span>
                        ))}
                        {document.tags.length > (viewMode === 'grid' ? 3 : 5) && (
                          <span className="text-xs text-muted-foreground">
                            +{document.tags.length - (viewMode === 'grid' ? 3 : 5)}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Stats */}
                    <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <Eye className="w-3 h-3" />
                        <span>{document.viewCount}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Download className="w-3 h-3" />
                        <span>{document.downloadCount}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Share2 className="w-3 h-3" />
                        <span>{document.shareCount}</span>
                      </div>
                    </div>

                    {/* Collaborators */}
                    {document.collaborators && document.collaborators.length > 0 && viewMode === 'grid' && (
                      <div className="flex items-center space-x-1 mt-2">
                        <Users className="w-3 h-3 text-muted-foreground" />
                        <div className="flex -space-x-1">
                          {document.collaborators.slice(0, 3).map((collaborator) => (
                            <div
                              key={collaborator.id}
                              className="w-5 h-5 rounded-full bg-muted border-2 border-background flex items-center justify-center"
                              title={collaborator.name}
                            >
                              {collaborator.avatar ? (
                                <Image
                                  src={collaborator.avatar}
                                  alt={collaborator.name}
                                  width={20}
                                  height={20}
                                  className="rounded-full"
                                />
                              ) : (
                                <User className="w-3 h-3 text-muted-foreground" />
                              )}
                            </div>
                          ))}
                          {document.collaborators.length > 3 && (
                            <div className="w-5 h-5 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs">
                              +{document.collaborators.length - 3}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
            <FileText className="w-6 h-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {t('documents:noDocumentsFound')}
          </h3>
          <p className="text-muted-foreground mb-4">
            {selectedFilter === 'all' 
              ? t('documents:noDocumentsDescription')
              : t('documents:noDocumentsForFilter')
            }
          </p>
          <div className="flex flex-col sm:flex-row gap-2 justify-center">
            <Link
              href="/upload"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 focus-visible-ring"
            >
              <Upload className="w-4 h-4" />
              <span>{t('documents:uploadFirst')}</span>
            </Link>
            {selectedFilter !== 'all' && (
              <button
                onClick={() => setSelectedFilter('all')}
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 focus-visible-ring"
              >
                {t('documents:showAllDocuments')}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Show more link */}
      {filteredDocuments.length >= limit && documents.length > limit && (
        <div className="text-center">
          <Link
            href="/documents"
            className="inline-flex items-center space-x-2 text-primary hover:text-primary/80 focus-visible-ring rounded"
          >
            <span>{t('documents:viewAllDocuments')}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  )
}