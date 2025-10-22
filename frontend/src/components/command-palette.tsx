import { useState, useEffect, useRef, useMemo } from 'react'
import { useTranslation } from 'next-i18next'
import { useRouter } from 'next/router'
import { useSession } from 'next-auth/react'
import {
  Search,
  Command,
  ArrowUp,
  ArrowDown,
  ArrowRight,
  Enter,
  Escape,
  Hash,
  AtSign,
  FileText,
  Folder,
  Upload,
  Download,
  Share2,
  Settings,
  Users,
  User,
  Bell,
  Star,
  Heart,
  Bookmark,
  Eye,
  Edit,
  Trash2,
  Copy,
  Cut,
  Paste,
  Undo,
  Redo,
  Save,
  Plus,
  Minus,
  X,
  Check,
  Home,
  Calendar,
  Clock,
  Mail,
  Phone,
  Globe,
  MapPin,
  Navigation,
  Compass,
  Map,
  Route,
  Target,
  Flag,
  Tag,
  Filter,
  SlidersHorizontal,
  BarChart3,
  PieChart,
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  Brain,
  Sparkles,
  Crown,
  Award,
  Trophy,
  Medal,
  Gem,
  Diamond,
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
  Umbrella,
  Wind,
  Thermometer,
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
  Image,
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
  Archive,
  FolderPlus,
  FilePlus,
  FileImage,
  FileVideo,
  FileAudio,
  FileSpreadsheet,
  FileBarChart,
  Link,
  ExternalLink,
  Maximize2,
  Minimize2,
  RotateCcw,
  RefreshCw,
  HelpCircle,
  Info,
  AlertCircle,
  CheckCircle,
  XCircle,
  Shield,
  Lock,
  Unlock,
  Key,
  LogIn,
  LogOut,
  UserPlus,
  UserMinus,
  UserCheck,
  UserX,
  MessageSquare,
  MessageCircle,
  Send,
  Inbox,
  Outbox,
  Archive as ArchiveIcon,
  Trash,
  Delete,
  Backspace,
  Space,
  Tab,
  CapsLock,
  Shift,
  Ctrl,
  Alt,
  Meta,
  Fn,
  PrintScreen,
  ScrollLock,
  Pause as PauseKey,
  Insert,
  End,
  PageUp,
  PageDown,
  F1,
  F2,
  F3,
  F4,
  F5,
  F6,
  F7,
  F8,
  F9,
  F10,
  F11,
  F12
} from 'lucide-react'

// Hooks
import { useDebounce } from '@/hooks/use-debounce'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  className?: string
}

interface Command {
  id: string
  title: string
  subtitle?: string
  description?: string
  icon: React.ComponentType<{ className?: string }>
  category: 'navigation' | 'actions' | 'documents' | 'settings' | 'help' | 'recent' | 'ai' | 'tools'
  keywords: string[]
  action: () => void | Promise<void>
  shortcut?: string[]
  href?: string
  disabled?: boolean
  premium?: boolean
  badge?: string
  priority?: number
  lastUsed?: Date
  usageCount?: number
}

interface Category {
  id: string
  title: string
  icon: React.ComponentType<{ className?: string }>
  description?: string
  commands: Command[]
}

export function CommandPalette({ open, onOpenChange, className }: CommandPaletteProps) {
  const { t } = useTranslation(['command-palette', 'common', 'navigation'])
  const router = useRouter()
  const { data: session } = useSession()
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [recentCommands, setRecentCommands] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const debouncedQuery = useDebounce(query, 150)

  // Define all available commands
  const allCommands: Command[] = useMemo(() => [
    // Navigation commands
    {
      id: 'nav-dashboard',
      title: t('command-palette:dashboard'),
      subtitle: t('command-palette:goToDashboard'),
      icon: Home,
      category: 'navigation',
      keywords: ['dashboard', 'home', 'main'],
      action: () => router.push('/'),
      href: '/',
      shortcut: ['g', 'd'],
      priority: 10
    },
    {
      id: 'nav-documents',
      title: t('command-palette:documents'),
      subtitle: t('command-palette:browseDocuments'),
      icon: FileText,
      category: 'navigation',
      keywords: ['documents', 'files', 'browse'],
      action: () => router.push('/documents'),
      href: '/documents',
      shortcut: ['g', 'f'],
      priority: 9
    },
    {
      id: 'nav-search',
      title: t('command-palette:search'),
      subtitle: t('command-palette:searchEverything'),
      icon: Search,
      category: 'navigation',
      keywords: ['search', 'find', 'lookup'],
      action: () => router.push('/search'),
      href: '/search',
      shortcut: ['/', 's'],
      priority: 8
    },
    {
      id: 'nav-collections',
      title: t('command-palette:collections'),
      subtitle: t('command-palette:manageCollections'),
      icon: Bookmark,
      category: 'navigation',
      keywords: ['collections', 'bookmarks', 'organize'],
      action: () => router.push('/collections'),
      href: '/collections',
      shortcut: ['g', 'c'],
      priority: 7
    },
    {
      id: 'nav-team',
      title: t('command-palette:team'),
      subtitle: t('command-palette:manageTeam'),
      icon: Users,
      category: 'navigation',
      keywords: ['team', 'users', 'members', 'collaborate'],
      action: () => router.push('/team'),
      href: '/team',
      shortcut: ['g', 't'],
      priority: 6
    },
    {
      id: 'nav-settings',
      title: t('command-palette:settings'),
      subtitle: t('command-palette:configureApp'),
      icon: Settings,
      category: 'navigation',
      keywords: ['settings', 'preferences', 'config'],
      action: () => router.push('/settings'),
      href: '/settings',
      shortcut: ['g', 's'],
      priority: 5
    },

    // Action commands
    {
      id: 'action-upload',
      title: t('command-palette:uploadDocument'),
      subtitle: t('command-palette:addNewFiles'),
      icon: Upload,
      category: 'actions',
      keywords: ['upload', 'add', 'import', 'file'],
      action: () => router.push('/upload'),
      href: '/upload',
      shortcut: ['u'],
      priority: 10
    },
    {
      id: 'action-chat',
      title: t('command-palette:startChat'),
      subtitle: t('command-palette:aiAssistant'),
      icon: MessageSquare,
      category: 'actions',
      keywords: ['chat', 'ai', 'assistant', 'ask'],
      action: () => router.push('/chat'),
      href: '/chat',
      shortcut: ['c'],
      priority: 9
    },
    {
      id: 'action-create-collection',
      title: t('command-palette:createCollection'),
      subtitle: t('command-palette:organizeDocuments'),
      icon: FolderPlus,
      category: 'actions',
      keywords: ['create', 'collection', 'folder', 'organize'],
      action: () => router.push('/collections/new'),
      href: '/collections/new',
      priority: 8
    },
    {
      id: 'action-invite-user',
      title: t('command-palette:inviteUser'),
      subtitle: t('command-palette:addTeamMember'),
      icon: UserPlus,
      category: 'actions',
      keywords: ['invite', 'user', 'team', 'member', 'collaborate'],
      action: () => router.push('/team/invite'),
      href: '/team/invite',
      priority: 7
    },
    {
      id: 'action-scan-document',
      title: t('command-palette:scanDocument'),
      subtitle: t('command-palette:useCamera'),
      icon: Camera,
      category: 'actions',
      keywords: ['scan', 'camera', 'ocr', 'capture'],
      action: () => router.push('/scan'),
      href: '/scan',
      priority: 6
    },

    // AI Commands
    {
      id: 'ai-insights',
      title: t('command-palette:aiInsights'),
      subtitle: t('command-palette:getSmartAnalysis'),
      icon: Brain,
      category: 'ai',
      keywords: ['ai', 'insights', 'analysis', 'smart'],
      action: () => router.push('/insights'),
      href: '/insights',
      premium: true,
      priority: 9
    },
    {
      id: 'ai-summarize',
      title: t('command-palette:summarizeContent'),
      subtitle: t('command-palette:generateSummary'),
      icon: Sparkles,
      category: 'ai',
      keywords: ['summarize', 'summary', 'ai', 'content'],
      action: async () => {
        // Trigger AI summarization
        announceAction(t('command-palette:aiSummarizationStarted'), 'polite')
      },
      priority: 8
    },
    {
      id: 'ai-translate',
      title: t('command-palette:translateContent'),
      subtitle: t('command-palette:multiLanguage'),
      icon: Globe,
      category: 'ai',
      keywords: ['translate', 'language', 'ai', 'multilingual'],
      action: async () => {
        // Trigger AI translation
        announceAction(t('command-palette:aiTranslationStarted'), 'polite')
      },
      priority: 7
    },

    // Tools commands
    {
      id: 'tool-export',
      title: t('command-palette:exportData'),
      subtitle: t('command-palette:downloadBackup'),
      icon: Download,
      category: 'tools',
      keywords: ['export', 'download', 'backup', 'data'],
      action: async () => {
        // Trigger export
        announceAction(t('command-palette:exportStarted'), 'polite')
      },
      priority: 6
    },
    {
      id: 'tool-analytics',
      title: t('command-palette:viewAnalytics'),
      subtitle: t('command-palette:usageStats'),
      icon: BarChart3,
      category: 'tools',
      keywords: ['analytics', 'stats', 'metrics', 'usage'],
      action: () => router.push('/analytics'),
      href: '/analytics',
      priority: 5
    },
    {
      id: 'tool-backup',
      title: t('command-palette:createBackup'),
      subtitle: t('command-palette:saveData'),
      icon: Archive,
      category: 'tools',
      keywords: ['backup', 'save', 'archive', 'preserve'],
      action: async () => {
        // Trigger backup
        announceAction(t('command-palette:backupStarted'), 'polite')
      },
      priority: 4
    },

    // Settings commands
    {
      id: 'settings-profile',
      title: t('command-palette:editProfile'),
      subtitle: t('command-palette:personalInfo'),
      icon: User,
      category: 'settings',
      keywords: ['profile', 'account', 'personal', 'info'],
      action: () => router.push('/settings/profile'),
      href: '/settings/profile',
      priority: 7
    },
    {
      id: 'settings-security',
      title: t('command-palette:security'),
      subtitle: t('command-palette:passwordSecurity'),
      icon: Shield,
      category: 'settings',
      keywords: ['security', 'password', 'auth', 'safety'],
      action: () => router.push('/settings/security'),
      href: '/settings/security',
      priority: 6
    },
    {
      id: 'settings-integrations',
      title: t('command-palette:integrations'),
      subtitle: t('command-palette:connectApps'),
      icon: Zap,
      category: 'settings',
      keywords: ['integrations', 'apps', 'connect', 'api'],
      action: () => router.push('/settings/integrations'),
      href: '/settings/integrations',
      priority: 5
    },
    {
      id: 'settings-billing',
      title: t('command-palette:billing'),
      subtitle: t('command-palette:subscription'),
      icon: Crown,
      category: 'settings',
      keywords: ['billing', 'subscription', 'payment', 'plan'],
      action: () => router.push('/settings/billing'),
      href: '/settings/billing',
      priority: 4
    },

    // Help commands
    {
      id: 'help-docs',
      title: t('command-palette:documentation'),
      subtitle: t('command-palette:learnMore'),
      icon: HelpCircle,
      category: 'help',
      keywords: ['help', 'docs', 'documentation', 'guide'],
      action: () => router.push('/docs'),
      href: '/docs',
      priority: 8
    },
    {
      id: 'help-shortcuts',
      title: t('command-palette:keyboardShortcuts'),
      subtitle: t('command-palette:shortcuts'),
      icon: Command,
      category: 'help',
      keywords: ['shortcuts', 'keyboard', 'hotkeys', 'commands'],
      action: () => {
        // Show shortcuts modal
        announceAction(t('command-palette:shortcutsOpened'), 'polite')
      },
      priority: 7
    },
    {
      id: 'help-support',
      title: t('command-palette:contactSupport'),
      subtitle: t('command-palette:getHelp'),
      icon: Mail,
      category: 'help',
      keywords: ['support', 'help', 'contact', 'assistance'],
      action: () => router.push('/support'),
      href: '/support',
      priority: 6
    },
    {
      id: 'help-feedback',
      title: t('command-palette:sendFeedback'),
      subtitle: t('command-palette:improveApp'),
      icon: MessageCircle,
      category: 'help',
      keywords: ['feedback', 'suggestions', 'improve', 'report'],
      action: () => {
        // Open feedback form
        announceAction(t('command-palette:feedbackOpened'), 'polite')
      },
      priority: 5
    }
  ], [t, router, announceAction])

  // Categories definition
  const categories: Category[] = useMemo(() => [
    {
      id: 'recent',
      title: t('command-palette:recent'),
      icon: Clock,
      description: t('command-palette:recentlyUsed'),
      commands: allCommands.filter(cmd => recentCommands.includes(cmd.id))
    },
    {
      id: 'navigation',
      title: t('command-palette:navigation'),
      icon: Navigation,
      description: t('command-palette:goToPages'),
      commands: allCommands.filter(cmd => cmd.category === 'navigation')
    },
    {
      id: 'actions',
      title: t('command-palette:actions'),
      icon: Zap,
      description: t('command-palette:quickActions'),
      commands: allCommands.filter(cmd => cmd.category === 'actions')
    },
    {
      id: 'ai',
      title: t('command-palette:ai'),
      icon: Brain,
      description: t('command-palette:aiFeatures'),
      commands: allCommands.filter(cmd => cmd.category === 'ai')
    },
    {
      id: 'tools',
      title: t('command-palette:tools'),
      icon: Settings,
      description: t('command-palette:utilityTools'),
      commands: allCommands.filter(cmd => cmd.category === 'tools')
    },
    {
      id: 'settings',
      title: t('command-palette:settings'),
      icon: SlidersHorizontal,
      description: t('command-palette:configOptions'),
      commands: allCommands.filter(cmd => cmd.category === 'settings')
    },
    {
      id: 'help',
      title: t('command-palette:help'),
      icon: HelpCircle,
      description: t('command-palette:helpResources'),
      commands: allCommands.filter(cmd => cmd.category === 'help')
    }
  ], [t, allCommands, recentCommands])

  // Filter commands based on query and category
  const filteredCommands = useMemo(() => {
    let commands = allCommands

    // Filter by category
    if (activeCategory !== 'all') {
      const category = categories.find(cat => cat.id === activeCategory)
      commands = category?.commands || []
    }

    // Filter by search query
    if (debouncedQuery.trim()) {
      const query = debouncedQuery.toLowerCase()
      commands = commands.filter(cmd => {
        const searchableText = [
          cmd.title,
          cmd.subtitle,
          cmd.description,
          ...cmd.keywords
        ].join(' ').toLowerCase()
        
        return searchableText.includes(query)
      })
    }

    // Sort by priority and usage
    return commands.sort((a, b) => {
      // Recent commands first
      if (recentCommands.includes(a.id) && !recentCommands.includes(b.id)) return -1
      if (!recentCommands.includes(a.id) && recentCommands.includes(b.id)) return 1
      
      // Then by priority
      const priorityA = a.priority || 0
      const priorityB = b.priority || 0
      if (priorityA !== priorityB) return priorityB - priorityA
      
      // Then by usage count
      const usageA = a.usageCount || 0
      const usageB = b.usageCount || 0
      if (usageA !== usageB) return usageB - usageA
      
      // Finally alphabetically
      return a.title.localeCompare(b.title)
    })
  }, [allCommands, categories, activeCategory, debouncedQuery, recentCommands])

  // Load recent commands from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('command-palette-recent')
      if (saved) {
        setRecentCommands(JSON.parse(saved))
      }
    } catch (error) {
      console.error('Failed to load recent commands:', error)
    }
  }, [])

  // Reset state when opening/closing
  useEffect(() => {
    if (open) {
      setQuery('')
      setSelectedIndex(0)
      setActiveCategory('all')
      inputRef.current?.focus()
    }
  }, [open])

  // Handle keyboard navigation
  useKeyboardShortcuts({
    'arrowdown': (e) => {
      if (open) {
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < filteredCommands.length - 1 ? prev + 1 : 0
        )
      }
    },
    'arrowup': (e) => {
      if (open) {
        e.preventDefault()
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : filteredCommands.length - 1
        )
      }
    },
    'enter': (e) => {
      if (open && filteredCommands[selectedIndex]) {
        e.preventDefault()
        executeCommand(filteredCommands[selectedIndex])
      }
    },
    'escape': () => {
      if (open) {
        onOpenChange(false)
      }
    },
    'tab': (e) => {
      if (open) {
        e.preventDefault()
        // Cycle through categories
        const currentIndex = categories.findIndex(cat => cat.id === activeCategory)
        const nextIndex = currentIndex < categories.length - 1 ? currentIndex + 1 : 0
        setActiveCategory(categories[nextIndex]?.id || 'all')
        setSelectedIndex(0)
      }
    }
  })

  // Execute command
  const executeCommand = async (command: Command) => {
    if (command.disabled) return

    try {
      setIsLoading(true)
      
      // Add to recent commands
      const newRecent = [command.id, ...recentCommands.filter(id => id !== command.id)].slice(0, 10)
      setRecentCommands(newRecent)
      localStorage.setItem('command-palette-recent', JSON.stringify(newRecent))

      // Update usage count
      const updatedCommand = { ...command, usageCount: (command.usageCount || 0) + 1 }
      
      // Execute the command
      await command.action()
      
      // Close palette
      onOpenChange(false)
      
      // Announce action
      announceAction(t('command-palette:commandExecuted', { command: command.title }), 'polite')
      
    } catch (error) {
      console.error('Failed to execute command:', error)
      announceAction(t('command-palette:commandFailed'), 'assertive')
    } finally {
      setIsLoading(false)
    }
  }

  // Format shortcut display
  const formatShortcut = (shortcut: string[]) => {
    const symbols: Record<string, string> = {
      'cmd': '⌘',
      'ctrl': '⌃',
      'alt': '⌥',
      'shift': '⇧',
      'enter': '↵',
      'escape': '⎋',
      'tab': '⇥',
      'space': '␣',
      'arrowup': '↑',
      'arrowdown': '↓',
      'arrowleft': '←',
      'arrowright': '→'
    }
    
    return shortcut.map(key => symbols[key.toLowerCase()] || key.toUpperCase()).join(' ')
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" dir={direction}>
      <div className="flex min-h-full items-start justify-center p-4 pt-[10vh]">
        <div
          ref={containerRef}
          className={cn(
            'w-full max-w-2xl bg-background border border-border rounded-xl shadow-2xl overflow-hidden',
            'animate-in fade-in-0 zoom-in-95 duration-200',
            className
          )}
        >
          {/* Search input */}
          <div className="flex items-center border-b border-border p-4">
            <Search className="w-5 h-5 text-muted-foreground me-3 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('command-palette:searchPlaceholder')}
              className="flex-1 bg-transparent text-lg placeholder:text-muted-foreground focus:outline-none"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
            />
            {isLoading && (
              <div className="w-4 h-4 border-2 border-muted-foreground border-t-transparent rounded-full animate-spin ms-2" />
            )}
          </div>

          {/* Category tabs */}
          <div className="flex overflow-x-auto border-b border-border">
            <button
              onClick={() => {
                setActiveCategory('all')
                setSelectedIndex(0)
              }}
              className={cn(
                'flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
                activeCategory === 'all'
                  ? 'border-primary text-primary bg-primary/10'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
              )}
            >
              <Command className="w-4 h-4" />
              <span>{t('command-palette:all')}</span>
            </button>
            {categories.map((category) => {
              const Icon = category.icon
              return (
                <button
                  key={category.id}
                  onClick={() => {
                    setActiveCategory(category.id)
                    setSelectedIndex(0)
                  }}
                  className={cn(
                    'flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
                    activeCategory === category.id
                      ? 'border-primary text-primary bg-primary/10'
                      : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                  )}
                  title={category.description}
                >
                  <Icon className="w-4 h-4" />
                  <span>{category.title}</span>
                  {category.commands.length > 0 && (
                    <span className="bg-muted text-muted-foreground rounded-full px-2 py-0.5 text-xs">
                      {category.commands.length}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Commands list */}
          <div className="max-h-96 overflow-y-auto">
            {filteredCommands.length > 0 ? (
              <div className="p-2">
                {filteredCommands.map((command, index) => {
                  const Icon = command.icon
                  return (
                    <button
                      key={command.id}
                      onClick={() => executeCommand(command)}
                      disabled={command.disabled}
                      className={cn(
                        'w-full flex items-center justify-between p-3 rounded-lg text-start transition-colors',
                        'focus-visible-ring disabled:opacity-50 disabled:cursor-not-allowed',
                        index === selectedIndex
                          ? 'bg-primary text-primary-foreground'
                          : 'hover:bg-muted'
                      )}
                    >
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <div className={cn(
                          'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                          index === selectedIndex
                            ? 'bg-primary-foreground/20'
                            : 'bg-muted'
                        )}>
                          <Icon className="w-4 h-4" />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium truncate">
                              {command.title}
                            </p>
                            {command.premium && (
                              <Crown className="w-3 h-3 text-yellow-500 flex-shrink-0" />
                            )}
                            {command.badge && (
                              <span className="bg-primary/20 text-primary px-1.5 py-0.5 rounded text-xs flex-shrink-0">
                                {command.badge}
                              </span>
                            )}
                            {recentCommands.includes(command.id) && (
                              <Clock className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                            )}
                          </div>
                          {command.subtitle && (
                            <p className={cn(
                              'text-xs truncate',
                              index === selectedIndex
                                ? 'text-primary-foreground/70'
                                : 'text-muted-foreground'
                            )}>
                              {command.subtitle}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Shortcut */}
                      {command.shortcut && (
                        <div className="flex items-center space-x-1 ms-2">
                          {command.shortcut.map((key, i) => (
                            <kbd
                              key={i}
                              className={cn(
                                'px-1.5 py-0.5 text-xs rounded border',
                                index === selectedIndex
                                  ? 'bg-primary-foreground/20 border-primary-foreground/30 text-primary-foreground'
                                  : 'bg-muted border-border text-muted-foreground'
                              )}
                            >
                              {formatShortcut([key])}
                            </kbd>
                          ))}
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center mb-4">
                  <Search className="w-5 h-5 text-muted-foreground" />
                </div>
                <h3 className="text-sm font-medium mb-1">
                  {t('command-palette:noResults')}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {query.trim() 
                    ? t('command-palette:noResultsForQuery', { query })
                    : t('command-palette:noCommandsInCategory')
                  }
                </p>
                <button
                  onClick={() => {
                    setQuery('')
                    setActiveCategory('all')
                    setSelectedIndex(0)
                  }}
                  className="mt-3 text-xs text-primary hover:text-primary/80 focus-visible-ring rounded"
                >
                  {t('command-palette:clearSearch')}
                </button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-3 border-t border-border bg-muted/30 text-xs text-muted-foreground">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-background border border-border rounded">↑↓</kbd>
                <span>{t('command-palette:navigate')}</span>
              </div>
              <div className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-background border border-border rounded">↵</kbd>
                <span>{t('command-palette:select')}</span>
              </div>
              <div className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-background border border-border rounded">⇥</kbd>
                <span>{t('command-palette:switchCategory')}</span>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              <kbd className="px-1.5 py-0.5 bg-background border border-border rounded">⎋</kbd>
              <span>{t('command-palette:close')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}