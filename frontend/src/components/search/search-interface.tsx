import { useState, useRef, useEffect, useCallback } from 'react'
import { useTranslation } from 'next-i18next'
import { useRouter } from 'next/router'
import {
  Search,
  Filter,
  X,
  Mic,
  MicOff,
  Sparkles,
  Loader,
  ChevronDown,
  History,
  Check,
  SlidersHorizontal,
  Brain,
  FileText,
  BarChart3,
  Calendar,
  User,
  Tag,
  Star,
  Edit,
  CheckCircle,
  Archive,
  Database,
  Globe,
  Video,
  Music
} from '@/lib/icon-mappings'
/*import {
  Search,
  Filter,
  SlidersHorizontal,
  Calendar,
  User,
  FileText,
  Tag,
  MapPin,
  Clock,
  TrendingUp,
  Star,
  Bookmark,
  Archive,
  Download,
  Share2,
  MoreHorizontal,
  ChevronDown,
  ChevronUp,
  X,
  Sparkles,
  Brain,
  Target,
  Zap,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Info,
  Loader2,
  Mic,
  MicOff,
  Camera,
  Image,
  Upload,
  History,
  BookOpen,
  Users,
  Building,
  Globe,
  Shield,
  Eye,
  EyeOff,
  Settings,
  HelpCircle,
  ExternalLink,
  Copy,
  Check,
  Plus,
  Minus,
  RotateCcw,
  Save,
  Heart,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Flag,
  Award,
  Crown,
  Layers,
  Grid3X3,
  List,
  BarChart3,
  PieChart,
  Activity,
  Database,
  Server,
  Cloud,
  Lock,
  Unlock,
  Key,
  UserCheck,
  UserX,
  Mail,
  Phone,
  Link,
  Code,
  Terminal,
  GitBranch,
  Package,
  Cpu,
  HardDrive,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Tv,
  Headphones,
  Speaker,
  Volume2,
  VolumeX,
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
  Music,
  Video,
  Camera as CameraIcon,
  Film,
  Gamepad2,
  Joystick,
  Dices,
  Puzzle,
  Trophy,
  Medal,
  Flame,
  Lightning,
  Sun,
  Moon,
  CloudRain,
  CloudSnow,
  Wind,
  Thermometer,
  Umbrella,
  Sunset,
  Sunrise,
  Mountain,
  Trees,
  Flower,
  Leaf,
  Sprout,
  Seedling,
  Cactus,
  PalmTree,
  Pine,
  Grass,
  Clover,
  Cherry,
  Apple,
  Banana,
  Grape,
  Orange,
  Lemon,
  Strawberry,
  Watermelon,
  Carrot,
  Corn,
  Pepper,
  Tomato,
  Potato,
  Onion,
  Garlic,
  Mushroom,
  Bread,
  Croissant,
  Bagel,
  Pretzel,
  Cheese,
  Egg,
  Bacon,
  Ham,
  Sausage,
  Chicken,
  Turkey,
  Beef,
  Fish,
  Shrimp,
  Crab,
  Lobster,
  Squid,
  Octopus,
  Whale,
  Dolphin,
  Shark,
  Turtle,
  Penguin,
  Bird,
  Eagle,
  Owl,
  Dove,
  Duck,
  Swan,
  Flamingo,
  Parrot,
  Peacock,
  Butterfly,
  Bee,
  Ladybug,
  Spider,
  Snail,
  Ant,
  Worm,
  Snake,
  Lizard,
  Frog,
  Mouse,
  Rat,
  Hamster,
  Rabbit,
  Cat,
  Dog,
  Horse,
  Cow,
  Pig,
  Sheep,
  Goat,
  Deer,
  Bear,
  Wolf,
  Fox,
  Lion,
  Tiger,
  Elephant,
  Giraffe,
  Zebra,
  Rhino,
  Hippo,
  Monkey,
  Gorilla,
  Panda,
  Koala,
  Kangaroo,
  Sloth,
  Bat,
  Hedgehog,
  Otter,
  Seal,
  Walrus,
  Narwhal,
  Unicorn,
  Dragon,
  Robot,
  Alien,
  Ghost,
  Skull,
  Zombie,
  Vampire,
  Witch,
  Wizard,
  Fairy,
  Angel,
  Devil,
  Demon,
  Genie,
  Mermaid,
  Superhero,
  Ninja,
  Pirate,
  Knight,
  Princess,
  Prince,
  King,
  Queen,
  Emperor,
  Pope,
  Monk,
  Nun,
  Priest,
  Rabbi,
  Imam,
  Buddha,
  Jesus,
  Mary,
  Saint,
  Prophet,
  God,
  Allah,
  Krishna,
  Shiva,
  Vishnu,
  Brahma,
  Ganesha,
  Hanuman,
  Lakshmi,
  Saraswati,
  Durga,
  Kali,
  Parvati,
  Sita,
  Rama,
  Arjuna,
  Bhima,
  Yudhishthira,
  Nakula,
  Sahadeva,
  Draupadi,
  Kunti,
  Gandhari,
  Dhritarashtra,
  Pandu,
  Karna,
  Duryodhana,
  Shakuni,
  Bhishma,
  Drona,
  Kripacharya,
  Ashwatthama,
  Parashurama,
  Kalki,
  Matsya,
  Kurma,
  Varaha,
  Narasimha,
  Vamana,
  Parashurama as ParashuramaAvatar,
  Rama as RamaAvatar,
  Krishna as KrishnaAvatar,
  Buddha as BuddhAvatar,
  Kalki as KalkiAvatar
} from '@/lib/icon-mappings'*/

// Hooks
import { useDebounce } from '@/hooks/use-debounce'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface SearchInterfaceProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  autoFocus?: boolean
  className?: string
  showAdvanced?: boolean
  showFilters?: boolean
  mode?: 'simple' | 'advanced' | 'ai'
  onModeChange?: (mode: 'simple' | 'advanced' | 'ai') => void
}

interface SearchFilter {
  id: string
  label: string
  type: 'select' | 'multiselect' | 'date' | 'daterange' | 'text' | 'number' | 'boolean' | 'slider'
  icon?: React.ComponentType<{ className?: string }>
  options?: Array<{ value: string; label: string; icon?: React.ComponentType<{ className?: string }> }>
  value?: any
  placeholder?: string
  min?: number
  max?: number
  step?: number
}

interface SearchSuggestion {
  id: string
  type: 'query' | 'document' | 'collection' | 'user' | 'tag' | 'recent' | 'trending'
  title: string
  description?: string
  icon: React.ComponentType<{ className?: string }>
  metadata?: {
    confidence?: number
    lastModified?: string
    author?: string
    tags?: string[]
    relevance?: number
    popularity?: number
  }
  onClick: () => void
}

interface SearchMode {
  id: 'simple' | 'advanced' | 'ai'
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  features: string[]
}

export function SearchInterface({
  value,
  onChange,
  placeholder = 'Search documents, collections, and more...',
  autoFocus = false,
  className,
  showAdvanced = true,
  showFilters = true,
  mode = 'simple',
  onModeChange
}: SearchInterfaceProps) {
  const { t } = useTranslation(['search', 'common'])
  const router = useRouter()
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [focused, setFocused] = useState(false)
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showModeSelector, setShowModeSelector] = useState(false)
  const [showFilterPanel, setShowFilterPanel] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1)

  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)
  const debouncedValue = useDebounce(value, 300)

  // Search modes configuration
  const searchModes: SearchMode[] = [
    {
      id: 'simple',
      label: t('search:simpleSearch'),
      description: t('search:simpleSearchDescription'),
      icon: Search,
      features: ['Quick search', 'Auto-complete', 'Recent searches']
    },
    {
      id: 'advanced',
      label: t('search:advancedSearch'),
      description: t('search:advancedSearchDescription'),
      icon: SlidersHorizontal,
      features: ['Filters', 'Boolean operators', 'Field-specific search']
    },
    {
      id: 'ai',
      label: t('search:aiSearch'),
      description: t('search:aiSearchDescription'),
      icon: Brain,
      features: ['Natural language', 'Semantic search', 'Smart suggestions']
    }
  ]

  // Search filters configuration
  const [filters, setFilters] = useState<SearchFilter[]>([
    {
      id: 'type',
      label: t('search:documentType'),
      type: 'multiselect',
      icon: FileText,
      options: [
        { value: 'pdf', label: 'PDF', icon: FileText },
        { value: 'doc', label: 'Word Document', icon: FileText },
        { value: 'ppt', label: 'Presentation', icon: FileText },
        { value: 'xlsx', label: 'Spreadsheet', icon: BarChart3 },
        { value: 'txt', label: 'Text File', icon: FileText },
        { value: 'image', label: 'Image', icon: Image },
        { value: 'video', label: 'Video', icon: Video },
        { value: 'audio', label: 'Audio', icon: Music }
      ],
      value: []
    },
    {
      id: 'dateRange',
      label: t('search:dateRange'),
      type: 'daterange',
      icon: Calendar,
      value: { start: null, end: null }
    },
    {
      id: 'author',
      label: t('search:author'),
      type: 'multiselect',
      icon: User,
      options: [
        { value: 'john-doe', label: 'John Doe', icon: User },
        { value: 'jane-smith', label: 'Jane Smith', icon: User },
        { value: 'mike-johnson', label: 'Mike Johnson', icon: User }
      ],
      value: []
    },
    {
      id: 'tags',
      label: t('search:tags'),
      type: 'multiselect',
      icon: Tag,
      options: [
        { value: 'important', label: 'Important', icon: Star },
        { value: 'draft', label: 'Draft', icon: Edit },
        { value: 'reviewed', label: 'Reviewed', icon: CheckCircle },
        { value: 'archived', label: 'Archived', icon: Archive }
      ],
      value: []
    },
    {
      id: 'size',
      label: t('search:fileSize'),
      type: 'slider',
      icon: Database,
      min: 0,
      max: 100,
      step: 1,
      value: [0, 100]
    },
    {
      id: 'language',
      label: t('search:language'),
      type: 'select',
      icon: Globe,
      options: [
        { value: 'any', label: 'Any Language' },
        { value: 'en', label: 'English' },
        { value: 'he', label: 'Hebrew' },
        { value: 'ar', label: 'Arabic' },
        { value: 'es', label: 'Spanish' },
        { value: 'fr', label: 'French' },
        { value: 'de', label: 'German' }
      ],
      value: 'any'
    }
  ])

  // Keyboard shortcuts
  useKeyboardShortcuts({
    'cmd+k': () => {
      inputRef.current?.focus()
    },
    'escape': () => {
      setFocused(false)
      setSelectedSuggestionIndex(-1)
      inputRef.current?.blur()
    },
    'arrowdown': (e) => {
      if (focused && suggestions.length > 0) {
        e.preventDefault()
        setSelectedSuggestionIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        )
      }
    },
    'arrowup': (e) => {
      if (focused && suggestions.length > 0) {
        e.preventDefault()
        setSelectedSuggestionIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        )
      }
    },
    'enter': (e) => {
      if (focused && selectedSuggestionIndex >= 0) {
        e.preventDefault()
        suggestions[selectedSuggestionIndex]?.onClick()
      }
    },
    'tab': (e) => {
      if (focused && selectedSuggestionIndex >= 0) {
        e.preventDefault()
        suggestions[selectedSuggestionIndex]?.onClick()
      }
    }
  })

  // Load suggestions based on input
  useEffect(() => {
    if (!debouncedValue.trim()) {
      setSuggestions([])
      setIsLoading(false)
      return
    }

    setIsLoading(true)

    // Mock suggestions - replace with actual API call
    const mockSuggestions: SearchSuggestion[] = [
      {
        id: 'doc-1',
        type: 'document',
        title: 'Product Requirements Document',
        description: 'Detailed specifications for the new dashboard feature',
        icon: FileText,
        metadata: {
          confidence: 0.95,
          lastModified: '2 days ago',
          author: 'John Doe',
          tags: ['product', 'requirements'],
          relevance: 0.9
        },
        onClick: () => router.push('/documents/prd-dashboard')
      },
      {
        id: 'collection-1',
        type: 'collection',
        title: 'Marketing Materials',
        description: '24 documents',
        icon: Bookmark,
        metadata: {
          popularity: 0.8
        },
        onClick: () => router.push('/collections/marketing-materials')
      },
      {
        id: 'user-1',
        type: 'user',
        title: 'Sarah Johnson',
        description: 'Product Manager',
        icon: User,
        onClick: () => router.push('/team/sarah-johnson')
      },
      {
        id: 'tag-1',
        type: 'tag',
        title: '#product-design',
        description: '156 documents',
        icon: Tag,
        onClick: () => router.push('/search?tag=product-design')
      }
    ]

    // Simulate API delay
    setTimeout(() => {
      setSuggestions(mockSuggestions.filter(s => 
        s.title.toLowerCase().includes(debouncedValue.toLowerCase()) ||
        s.description?.toLowerCase().includes(debouncedValue.toLowerCase())
      ))
      setIsLoading(false)
    }, 150)
  }, [debouncedValue, router])

  // Voice search functionality
  const handleVoiceSearch = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      announceAction(t('search:voiceNotSupported'), 'assertive')
      return
    }

    const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition
    const recognition = new SpeechRecognition()

    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = router.locale || 'en-US'

    recognition.onstart = () => {
      setIsListening(true)
      announceAction(t('search:listeningStarted'), 'polite')
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      onChange(transcript)
      announceAction(t('search:voiceInputReceived', { text: transcript }), 'polite')
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      announceAction(t('search:voiceError'), 'assertive')
    }

    recognition.onend = () => {
      setIsListening(false)
      announceAction(t('search:listeningEnded'), 'polite')
    }

    recognition.start()
  }, [onChange, router.locale, announceAction, t])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim()) {
      // Add to recent searches
      setRecentSearches(prev => {
        const updated = [value, ...prev.filter(s => s !== value)].slice(0, 10)
        localStorage.setItem('recentSearches', JSON.stringify(updated))
        return updated
      })

      // Navigate to search results
      router.push(`/search?q=${encodeURIComponent(value)}`)
      setFocused(false)
      announceAction(t('search:searchSubmitted'), 'polite')
    }
  }

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    suggestion.onClick()
    setFocused(false)
    setSelectedSuggestionIndex(-1)
  }

  const handleModeSelect = (newMode: typeof mode) => {
    onModeChange?.(newMode)
    setShowModeSelector(false)
    announceAction(t('search:modeChanged', { mode: newMode }), 'polite')
  }

  const getSuggestionIcon = (type: SearchSuggestion['type']) => {
    switch (type) {
      case 'document': return FileText
      case 'collection': return Bookmark
      case 'user': return User
      case 'tag': return Tag
      case 'recent': return History
      case 'trending': return TrendingUp
      default: return Search
    }
  }

  const currentMode = searchModes.find(m => m.id === mode) || searchModes[0]
  const ModeIcon = currentMode.icon

  return (
    <div className={cn('relative w-full', className)} dir={direction}>
      {/* Search Mode Selector */}
      {showAdvanced && (
        <div className="flex items-center space-x-2 mb-4">
          <div className="relative">
            <button
              onClick={() => setShowModeSelector(!showModeSelector)}
              className="flex items-center space-x-2 px-3 py-2 bg-muted rounded-lg hover:bg-muted/80 focus-visible-ring"
              aria-expanded={showModeSelector}
              aria-haspopup="listbox"
            >
              <ModeIcon className="w-4 h-4" />
              <span className="text-sm font-medium">{currentMode.label}</span>
              <ChevronDown className="w-3 h-3" />
            </button>

            {showModeSelector && (
              <div className="absolute top-full left-0 mt-1 w-80 bg-popover border border-border rounded-lg shadow-lg z-50">
                <div className="p-1" role="listbox">
                  {searchModes.map((searchMode) => {
                    const Icon = searchMode.icon
                    return (
                      <button
                        key={searchMode.id}
                        onClick={() => handleModeSelect(searchMode.id)}
                        className="w-full flex items-start space-x-3 p-3 rounded-md hover:bg-accent focus-visible-ring text-start"
                        role="option"
                        aria-selected={mode === searchMode.id}
                      >
                        <Icon className="w-5 h-5 mt-0.5 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{searchMode.label}</p>
                          <p className="text-xs text-muted-foreground mb-2">
                            {searchMode.description}
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {searchMode.features.map((feature, index) => (
                              <span 
                                key={index}
                                className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded"
                              >
                                {feature}
                              </span>
                            ))}
                          </div>
                        </div>
                        {mode === searchMode.id && (
                          <Check className="w-4 h-4 text-primary" />
                        )}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {showFilters && (
            <button
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className={cn(
                'flex items-center space-x-2 px-3 py-2 rounded-lg focus-visible-ring',
                showFilterPanel 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted hover:bg-muted/80'
              )}
              aria-expanded={showFilterPanel}
            >
              <Filter className="w-4 h-4" />
              <span className="text-sm">{t('search:filters')}</span>
            </button>
          )}
        </div>
      )}

      {/* Main Search Input */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute start-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          
          <input
            ref={inputRef}
            type="search"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setFocused(true)}
            placeholder={placeholder}
            autoFocus={autoFocus}
            className={cn(
              'w-full ps-12 pe-24 py-4 text-lg bg-background border-2 border-border rounded-xl',
              'focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none',
              'transition-all duration-200',
              focused && 'border-primary ring-2 ring-primary/20'
            )}
            aria-label={t('search:searchInput')}
            aria-expanded={focused && (suggestions.length > 0 || value.length > 0)}
            aria-haspopup="listbox"
            autoComplete="off"
            spellCheck="false"
          />

          <div className="absolute end-4 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
            {isLoading && (
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            )}
            
            {/* Voice search button */}
            <button
              type="button"
              onClick={handleVoiceSearch}
              className={cn(
                'p-2 rounded-lg hover:bg-accent focus-visible-ring',
                isListening && 'text-red-500 animate-pulse'
              )}
              aria-label={
                isListening 
                  ? t('search:stopListening')
                  : t('search:startVoiceSearch')
              }
              title={t('search:voiceSearch')}
            >
              {isListening ? (
                <MicOff className="w-4 h-4" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
            </button>

            {/* Advanced features for AI mode */}
            {mode === 'ai' && (
              <button
                type="button"
                className="p-2 rounded-lg hover:bg-accent focus-visible-ring"
                aria-label={t('search:aiInsights')}
                title={t('search:aiInsights')}
              >
                <Sparkles className="w-4 h-4 text-purple-500" />
              </button>
            )}

            {/* Search shortcut indicator */}
            <div className="hidden sm:flex items-center space-x-1 text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
              <kbd>⌘</kbd>
              <kbd>K</kbd>
            </div>
          </div>
        </div>

        {/* Search Suggestions Dropdown */}
        {focused && (suggestions.length > 0 || value.length > 0 || recentSearches.length > 0) && (
          <div 
            ref={suggestionsRef}
            className="absolute top-full left-0 right-0 mt-2 bg-popover border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto"
          >
            {/* Recent searches */}
            {value.length === 0 && recentSearches.length > 0 && (
              <div className="p-3 border-b border-border">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">
                  {t('search:recentSearches')}
                </h3>
                <div className="space-y-1">
                  {recentSearches.slice(0, 5).map((search, index) => (
                    <button
                      key={index}
                      onClick={() => onChange(search)}
                      className="flex items-center space-x-2 w-full p-2 rounded-md hover:bg-accent focus-visible-ring text-start"
                    >
                      <History className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm">{search}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <div className="p-1" role="listbox">
                {suggestions.map((suggestion, index) => {
                  const Icon = getSuggestionIcon(suggestion.type)
                  return (
                    <button
                      key={suggestion.id}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className={cn(
                        'w-full flex items-start space-x-3 p-3 rounded-md hover:bg-accent focus-visible-ring text-start',
                        selectedSuggestionIndex === index && 'bg-accent'
                      )}
                      role="option"
                      aria-selected={selectedSuggestionIndex === index}
                    >
                      <Icon className="w-4 h-4 mt-1 text-muted-foreground flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <p className="text-sm font-medium truncate">
                            {suggestion.title}
                          </p>
                          {suggestion.metadata?.confidence && (
                            <span className="text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded">
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
            )}

            {/* No results */}
            {value.length > 0 && suggestions.length === 0 && !isLoading && (
              <div className="p-6 text-center">
                <Search className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                <p className="text-sm text-muted-foreground">
                  {t('search:noSuggestions')}
                </p>
                <button
                  onClick={() => router.push(`/search?q=${encodeURIComponent(value)}`)}
                  className="mt-2 text-primary hover:underline text-sm focus-visible-ring rounded"
                >
                  {t('search:searchAnyway')}
                </button>
              </div>
            )}
          </div>
        )}
      </form>

      {/* Filter Panel */}
      {showFilterPanel && (
        <div className="mt-4 p-4 bg-muted/50 border border-border rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium">{t('search:advancedFilters')}</h3>
            <button
              onClick={() => setShowFilterPanel(false)}
              className="p-1 hover:bg-accent rounded focus-visible-ring"
              aria-label={t('search:closeFilters')}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filters.map((filter) => {
              const Icon = filter.icon
              return (
                <div key={filter.id} className="space-y-2">
                  <label className="flex items-center space-x-2 text-sm font-medium">
                    {Icon && <Icon className="w-4 h-4" />}
                    <span>{filter.label}</span>
                  </label>
                  
                  {filter.type === 'select' && (
                    <select
                      value={filter.value}
                      onChange={(e) => {
                        const updatedFilters = filters.map(f =>
                          f.id === filter.id ? { ...f, value: e.target.value } : f
                        )
                        setFilters(updatedFilters)
                      }}
                      className="w-full px-3 py-2 bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary"
                    >
                      {filter.options?.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  )}

                  {filter.type === 'multiselect' && (
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {filter.options?.map((option) => {
                        const OptionIcon = option.icon
                        return (
                          <label 
                            key={option.value}
                            className="flex items-center space-x-2 p-2 hover:bg-accent rounded cursor-pointer"
                          >
                            <input
                              type="checkbox"
                              checked={(filter.value as string[]).includes(option.value)}
                              onChange={(e) => {
                                const currentValues = filter.value as string[]
                                const newValues = e.target.checked
                                  ? [...currentValues, option.value]
                                  : currentValues.filter(v => v !== option.value)
                                
                                const updatedFilters = filters.map(f =>
                                  f.id === filter.id ? { ...f, value: newValues } : f
                                )
                                setFilters(updatedFilters)
                              }}
                              className="rounded border-border focus:ring-primary"
                            />
                            {OptionIcon && <OptionIcon className="w-4 h-4" />}
                            <span className="text-sm">{option.label}</span>
                          </label>
                        )
                      })}
                    </div>
                  )}

                  {filter.type === 'text' && (
                    <input
                      type="text"
                      value={filter.value || ''}
                      onChange={(e) => {
                        const updatedFilters = filters.map(f =>
                          f.id === filter.id ? { ...f, value: e.target.value } : f
                        )
                        setFilters(updatedFilters)
                      }}
                      placeholder={filter.placeholder}
                      className="w-full px-3 py-2 bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary"
                    />
                  )}

                  {filter.type === 'daterange' && (
                    <div className="flex space-x-2">
                      <input
                        type="date"
                        value={filter.value?.start || ''}
                        onChange={(e) => {
                          const updatedFilters = filters.map(f =>
                            f.id === filter.id 
                              ? { ...f, value: { ...f.value, start: e.target.value } }
                              : f
                          )
                          setFilters(updatedFilters)
                        }}
                        className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary"
                      />
                      <input
                        type="date"
                        value={filter.value?.end || ''}
                        onChange={(e) => {
                          const updatedFilters = filters.map(f =>
                            f.id === filter.id 
                              ? { ...f, value: { ...f.value, end: e.target.value } }
                              : f
                          )
                          setFilters(updatedFilters)
                        }}
                        className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary"
                      />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <button
              onClick={() => {
                // Reset all filters
                const resetFilters = filters.map(filter => ({
                  ...filter,
                  value: filter.type === 'multiselect' ? [] : 
                         filter.type === 'daterange' ? { start: null, end: null } :
                         filter.type === 'slider' ? [filter.min || 0, filter.max || 100] :
                         filter.options?.[0]?.value || ''
                }))
                setFilters(resetFilters)
              }}
              className="text-sm text-muted-foreground hover:text-foreground focus-visible-ring rounded"
            >
              {t('search:resetFilters')}
            </button>
            
            <button
              onClick={handleSubmit}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus-visible-ring"
            >
              {t('search:applyFilters')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}