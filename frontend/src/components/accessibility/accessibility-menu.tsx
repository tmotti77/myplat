import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'next-i18next'
import {
  Accessibility,
  Eye,
  EyeOff,
  Type,
  Contrast,
  Volume2,
  VolumeX,
  MousePointer,
  Keyboard,
  Focus,
  Palette,
  Settings,
  RotateCcw,
  Zap,
  Plus,
  Minus,
  Sun,
  Moon,
  Monitor,
  Languages,
  Navigation,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Play,
  Pause,
  Square,
  SkipBack,
  SkipForward,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Move,
  RotateCw,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  Target,
  Crosshair,
  Circle,
  X,
  Check,
  Info,
  HelpCircle,
  AlertCircle,
  CheckCircle,
  XCircle,
  Save,
  Download,
  Upload,
  RefreshCw,
  Power,
  PowerOff,
  Lightbulb,
  Clock,
  Timer,
  Calendar,
  Bell,
  BellOff,
  Mic,
  MicOff,
  Speaker,
  Headphones,
  Users,
  User,
  Shield,
  Lock,
  Unlock,
  Key,
  Home,
  Search,
  Menu,
  MoreHorizontal,
  Filter,
  SlidersHorizontal,
  Grid3X3,
  List,
  BarChart3,
  PieChart,
  Activity,
  TrendingUp,
  TrendingDown,
  Award,
  Trophy,
  Medal,
  Crown,
  Star,
  Heart,
  Bookmark,
  Share2,
  Link,
  ExternalLink,
  Copy,
  Scissors,
  Clipboard,
  Edit,
  Trash2,
  Archive,
  FolderPlus,
  FilePlus,
  FileText,
  Image,
  Video,
  Music,
  Camera,
  Film,
  Database,
  Server,
  HardDrive,
  Cpu,
  Monitor as MonitorIcon,
  Smartphone,
  Tablet,
  Laptop,
  Wifi,
  Bluetooth,
  Battery,
  Signal,
  Gauge,
  Thermometer,
  Wind,
  CloudRain,
  Sun as SunIcon,
  Moon as MoonIcon,
  Star as StarIcon,
  Cloud,
  CloudSnow,
  Snowflake,
  Umbrella,
  Droplets,
  Waves,
  Mountain,
  Trees,
  Flower,
  Leaf,
  Sprout,
  Globe,
  Map,
  MapPin,
  Navigation as NavigationIcon,
  Compass,
  Route,
  Flag,
  Anchor,
  Plane,
  Car,
  Truck,
  Bus,
  Train,
  Ship,
  Rocket,
  Bike,
  Footprints,
  Building,
  Home as HomeIcon,
  Store,
  Factory,
  School,
  GraduationCap,
  Hospital,
  Church,
  Landmark,
  Castle,
  Bridge,
  Tower
} from 'lucide-react'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useTheme } from '@/components/providers/theme-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface AccessibilityMenuProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  className?: string
}

interface AccessibilityOption {
  id: string
  category: 'visual' | 'audio' | 'motor' | 'cognitive' | 'navigation' | 'preferences'
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  type: 'toggle' | 'slider' | 'select' | 'button'
  value?: any
  options?: Array<{ value: any; label: string; description?: string }>
  min?: number
  max?: number
  step?: number
  unit?: string
  shortcut?: string[]
  premium?: boolean
  onChange?: (value: any) => void
  onAction?: () => void
}

export function AccessibilityMenu({ open, onOpenChange, className }: AccessibilityMenuProps) {
  const { t } = useTranslation(['accessibility', 'common'])
  const { theme, setTheme } = useTheme()
  const { direction, setDirection } = useRTL()
  const {
    preferences,
    updatePreferences,
    announceAction,
    enableHighContrast,
    disableHighContrast,
    enableReducedMotion,
    disableReducedMotion,
    enableScreenReader,
    disableScreenReader
  } = useAccessibility()

  const [activeCategory, setActiveCategory] = useState<string>('visual')
  const [searchQuery, setSearchQuery] = useState('')
  const [presets, setPresets] = useState<string[]>([])
  const [isApplying, setIsApplying] = useState(false)

  const containerRef = useRef<HTMLDivElement>(null)

  // Accessibility options configuration
  const options: AccessibilityOption[] = [
    // Visual options
    {
      id: 'high-contrast',
      category: 'visual',
      title: t('accessibility:highContrast'),
      description: t('accessibility:highContrastDesc'),
      icon: Contrast,
      type: 'toggle',
      value: preferences.highContrast,
      onChange: (enabled) => {
        if (enabled) {
          enableHighContrast()
        } else {
          disableHighContrast()
        }
        announceAction(
          enabled 
            ? t('accessibility:highContrastEnabled')
            : t('accessibility:highContrastDisabled'),
          'polite'
        )
      },
      shortcut: ['alt', 'h']
    },
    {
      id: 'font-size',
      category: 'visual',
      title: t('accessibility:fontSize'),
      description: t('accessibility:fontSizeDesc'),
      icon: Type,
      type: 'slider',
      value: preferences.fontSize || 16,
      min: 12,
      max: 24,
      step: 1,
      unit: 'px',
      onChange: (size) => {
        updatePreferences({ fontSize: size })
        document.documentElement.style.fontSize = `${size}px`
        announceAction(t('accessibility:fontSizeChanged', { size }), 'polite')
      }
    },
    {
      id: 'zoom-level',
      category: 'visual',
      title: t('accessibility:zoomLevel'),
      description: t('accessibility:zoomLevelDesc'),
      icon: ZoomIn,
      type: 'slider',
      value: preferences.zoomLevel || 100,
      min: 75,
      max: 200,
      step: 25,
      unit: '%',
      onChange: (zoom) => {
        updatePreferences({ zoomLevel: zoom })
        document.body.style.zoom = `${zoom}%`
        announceAction(t('accessibility:zoomLevelChanged', { zoom }), 'polite')
      }
    },
    {
      id: 'color-theme',
      category: 'visual',
      title: t('accessibility:colorTheme'),
      description: t('accessibility:colorThemeDesc'),
      icon: Palette,
      type: 'select',
      value: theme,
      options: [
        { value: 'light', label: t('accessibility:lightTheme'), description: t('accessibility:lightThemeDesc') },
        { value: 'dark', label: t('accessibility:darkTheme'), description: t('accessibility:darkThemeDesc') },
        { value: 'system', label: t('accessibility:systemTheme'), description: t('accessibility:systemThemeDesc') }
      ],
      onChange: (newTheme) => {
        setTheme(newTheme)
        announceAction(t('accessibility:themeChanged', { theme: newTheme }), 'polite')
      }
    },
    {
      id: 'reduce-motion',
      category: 'visual',
      title: t('accessibility:reduceMotion'),
      description: t('accessibility:reduceMotionDesc'),
      icon: Pause,
      type: 'toggle',
      value: preferences.reducedMotion,
      onChange: (enabled) => {
        if (enabled) {
          enableReducedMotion()
        } else {
          disableReducedMotion()
        }
        announceAction(
          enabled 
            ? t('accessibility:reducedMotionEnabled')
            : t('accessibility:reducedMotionDisabled'),
          'polite'
        )
      },
      shortcut: ['alt', 'm']
    },
    {
      id: 'focus-indicators',
      category: 'visual',
      title: t('accessibility:focusIndicators'),
      description: t('accessibility:focusIndicatorsDesc'),
      icon: Focus,
      type: 'toggle',
      value: preferences.enhancedFocus,
      onChange: (enabled) => {
        updatePreferences({ enhancedFocus: enabled })
        if (enabled) {
          document.documentElement.classList.add('enhanced-focus')
        } else {
          document.documentElement.classList.remove('enhanced-focus')
        }
        announceAction(
          enabled 
            ? t('accessibility:focusIndicatorsEnabled')
            : t('accessibility:focusIndicatorsDisabled'),
          'polite'
        )
      }
    },

    // Audio options
    {
      id: 'screen-reader',
      category: 'audio',
      title: t('accessibility:screenReader'),
      description: t('accessibility:screenReaderDesc'),
      icon: Volume2,
      type: 'toggle',
      value: preferences.screenReaderMode,
      onChange: (enabled) => {
        if (enabled) {
          enableScreenReader()
        } else {
          disableScreenReader()
        }
        announceAction(
          enabled 
            ? t('accessibility:screenReaderEnabled')
            : t('accessibility:screenReaderDisabled'),
          'polite'
        )
      },
      shortcut: ['alt', 's']
    },
    {
      id: 'audio-descriptions',
      category: 'audio',
      title: t('accessibility:audioDescriptions'),
      description: t('accessibility:audioDescriptionsDesc'),
      icon: Speaker,
      type: 'toggle',
      value: preferences.audioDescriptions,
      onChange: (enabled) => {
        updatePreferences({ audioDescriptions: enabled })
        announceAction(
          enabled 
            ? t('accessibility:audioDescriptionsEnabled')
            : t('accessibility:audioDescriptionsDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'sound-feedback',
      category: 'audio',
      title: t('accessibility:soundFeedback'),
      description: t('accessibility:soundFeedbackDesc'),
      icon: Bell,
      type: 'toggle',
      value: preferences.soundFeedback,
      onChange: (enabled) => {
        updatePreferences({ soundFeedback: enabled })
        announceAction(
          enabled 
            ? t('accessibility:soundFeedbackEnabled')
            : t('accessibility:soundFeedbackDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'speech-rate',
      category: 'audio',
      title: t('accessibility:speechRate'),
      description: t('accessibility:speechRateDesc'),
      icon: Gauge,
      type: 'slider',
      value: preferences.speechRate || 1,
      min: 0.5,
      max: 2,
      step: 0.1,
      unit: 'x',
      onChange: (rate) => {
        updatePreferences({ speechRate: rate })
        // Apply to speech synthesis if available
        if ('speechSynthesis' in window) {
          window.speechSynthesis.cancel()
        }
        announceAction(t('accessibility:speechRateChanged', { rate }), 'polite')
      }
    },

    // Motor options
    {
      id: 'keyboard-navigation',
      category: 'motor',
      title: t('accessibility:keyboardNavigation'),
      description: t('accessibility:keyboardNavigationDesc'),
      icon: Keyboard,
      type: 'toggle',
      value: preferences.keyboardNavigation,
      onChange: (enabled) => {
        updatePreferences({ keyboardNavigation: enabled })
        if (enabled) {
          document.documentElement.classList.add('keyboard-navigation')
        } else {
          document.documentElement.classList.remove('keyboard-navigation')
        }
        announceAction(
          enabled 
            ? t('accessibility:keyboardNavigationEnabled')
            : t('accessibility:keyboardNavigationDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'sticky-keys',
      category: 'motor',
      title: t('accessibility:stickyKeys'),
      description: t('accessibility:stickyKeysDesc'),
      icon: Key,
      type: 'toggle',
      value: preferences.stickyKeys,
      onChange: (enabled) => {
        updatePreferences({ stickyKeys: enabled })
        announceAction(
          enabled 
            ? t('accessibility:stickyKeysEnabled')
            : t('accessibility:stickyKeysDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'mouse-keys',
      category: 'motor',
      title: t('accessibility:mouseKeys'),
      description: t('accessibility:mouseKeysDesc'),
      icon: MousePointer,
      type: 'toggle',
      value: preferences.mouseKeys,
      onChange: (enabled) => {
        updatePreferences({ mouseKeys: enabled })
        announceAction(
          enabled 
            ? t('accessibility:mouseKeysEnabled')
            : t('accessibility:mouseKeysDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'click-timeout',
      category: 'motor',
      title: t('accessibility:clickTimeout'),
      description: t('accessibility:clickTimeoutDesc'),
      icon: Timer,
      type: 'slider',
      value: preferences.clickTimeout || 500,
      min: 100,
      max: 2000,
      step: 100,
      unit: 'ms',
      onChange: (timeout) => {
        updatePreferences({ clickTimeout: timeout })
        announceAction(t('accessibility:clickTimeoutChanged', { timeout }), 'polite')
      }
    },

    // Cognitive options
    {
      id: 'reading-guide',
      category: 'cognitive',
      title: t('accessibility:readingGuide'),
      description: t('accessibility:readingGuideDesc'),
      icon: Target,
      type: 'toggle',
      value: preferences.readingGuide,
      onChange: (enabled) => {
        updatePreferences({ readingGuide: enabled })
        if (enabled) {
          document.documentElement.classList.add('reading-guide')
        } else {
          document.documentElement.classList.remove('reading-guide')
        }
        announceAction(
          enabled 
            ? t('accessibility:readingGuideEnabled')
            : t('accessibility:readingGuideDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'dyslexia-font',
      category: 'cognitive',
      title: t('accessibility:dyslexiaFont'),
      description: t('accessibility:dyslexiaFontDesc'),
      icon: Type,
      type: 'toggle',
      value: preferences.dyslexiaFont,
      onChange: (enabled) => {
        updatePreferences({ dyslexiaFont: enabled })
        if (enabled) {
          document.documentElement.classList.add('dyslexia-font')
        } else {
          document.documentElement.classList.remove('dyslexia-font')
        }
        announceAction(
          enabled 
            ? t('accessibility:dyslexiaFontEnabled')
            : t('accessibility:dyslexiaFontDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'content-pause',
      category: 'cognitive',
      title: t('accessibility:contentPause'),
      description: t('accessibility:contentPauseDesc'),
      icon: Pause,
      type: 'toggle',
      value: preferences.contentPause,
      onChange: (enabled) => {
        updatePreferences({ contentPause: enabled })
        announceAction(
          enabled 
            ? t('accessibility:contentPauseEnabled')
            : t('accessibility:contentPauseDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'simplified-ui',
      category: 'cognitive',
      title: t('accessibility:simplifiedUI'),
      description: t('accessibility:simplifiedUIDesc'),
      icon: Minimize2,
      type: 'toggle',
      value: preferences.simplifiedUI,
      onChange: (enabled) => {
        updatePreferences({ simplifiedUI: enabled })
        if (enabled) {
          document.documentElement.classList.add('simplified-ui')
        } else {
          document.documentElement.classList.remove('simplified-ui')
        }
        announceAction(
          enabled 
            ? t('accessibility:simplifiedUIEnabled')
            : t('accessibility:simplifiedUIDisabled'),
          'polite'
        )
      }
    },

    // Navigation options
    {
      id: 'skip-links',
      category: 'navigation',
      title: t('accessibility:skipLinks'),
      description: t('accessibility:skipLinksDesc'),
      icon: SkipForward,
      type: 'toggle',
      value: preferences.skipLinks,
      onChange: (enabled) => {
        updatePreferences({ skipLinks: enabled })
        if (enabled) {
          document.documentElement.classList.add('show-skip-links')
        } else {
          document.documentElement.classList.remove('show-skip-links')
        }
        announceAction(
          enabled 
            ? t('accessibility:skipLinksEnabled')
            : t('accessibility:skipLinksDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'landmark-navigation',
      category: 'navigation',
      title: t('accessibility:landmarkNavigation'),
      description: t('accessibility:landmarkNavigationDesc'),
      icon: Navigation,
      type: 'toggle',
      value: preferences.landmarkNavigation,
      onChange: (enabled) => {
        updatePreferences({ landmarkNavigation: enabled })
        announceAction(
          enabled 
            ? t('accessibility:landmarkNavigationEnabled')
            : t('accessibility:landmarkNavigationDisabled'),
          'polite'
        )
      }
    },
    {
      id: 'heading-navigation',
      category: 'navigation',
      title: t('accessibility:headingNavigation'),
      description: t('accessibility:headingNavigationDesc'),
      icon: List,
      type: 'toggle',
      value: preferences.headingNavigation,
      onChange: (enabled) => {
        updatePreferences({ headingNavigation: enabled })
        announceAction(
          enabled 
            ? t('accessibility:headingNavigationEnabled')
            : t('accessibility:headingNavigationDisabled'),
          'polite'
        )
      }
    },

    // Preferences
    {
      id: 'language-direction',
      category: 'preferences',
      title: t('accessibility:languageDirection'),
      description: t('accessibility:languageDirectionDesc'),
      icon: Languages,
      type: 'select',
      value: direction,
      options: [
        { value: 'ltr', label: t('accessibility:leftToRight'), description: t('accessibility:ltrDesc') },
        { value: 'rtl', label: t('accessibility:rightToLeft'), description: t('accessibility:rtlDesc') }
      ],
      onChange: (newDirection) => {
        setDirection(newDirection)
        announceAction(t('accessibility:directionChanged', { direction: newDirection }), 'polite')
      }
    },
    {
      id: 'auto-save',
      category: 'preferences',
      title: t('accessibility:autoSave'),
      description: t('accessibility:autoSaveDesc'),
      icon: Save,
      type: 'toggle',
      value: preferences.autoSave,
      onChange: (enabled) => {
        updatePreferences({ autoSave: enabled })
        announceAction(
          enabled 
            ? t('accessibility:autoSaveEnabled')
            : t('accessibility:autoSaveDisabled'),
          'polite'
        )
      }
    }
  ]

  const categories = [
    { id: 'visual', label: t('accessibility:visual'), icon: Eye, description: t('accessibility:visualDesc') },
    { id: 'audio', label: t('accessibility:audio'), icon: Volume2, description: t('accessibility:audioDesc') },
    { id: 'motor', label: t('accessibility:motor'), icon: MousePointer, description: t('accessibility:motorDesc') },
    { id: 'cognitive', label: t('accessibility:cognitive'), icon: Target, description: t('accessibility:cognitiveDesc') },
    { id: 'navigation', label: t('accessibility:navigation'), icon: Navigation, description: t('accessibility:navigationDesc') },
    { id: 'preferences', label: t('accessibility:preferences'), icon: Settings, description: t('accessibility:preferencesDesc') }
  ]

  const accessibilityPresets = [
    {
      id: 'low-vision',
      name: t('accessibility:lowVision'),
      description: t('accessibility:lowVisionDesc'),
      settings: {
        highContrast: true,
        fontSize: 20,
        zoomLevel: 150,
        enhancedFocus: true,
        screenReaderMode: true
      }
    },
    {
      id: 'motor-impairment',
      name: t('accessibility:motorImpairment'),
      description: t('accessibility:motorImpairmentDesc'),
      settings: {
        keyboardNavigation: true,
        stickyKeys: true,
        mouseKeys: true,
        clickTimeout: 1000,
        enhancedFocus: true
      }
    },
    {
      id: 'cognitive-support',
      name: t('accessibility:cognitiveSupport'),
      description: t('accessibility:cognitiveSupportDesc'),
      settings: {
        simplifiedUI: true,
        readingGuide: true,
        reducedMotion: true,
        contentPause: true,
        dyslexiaFont: true
      }
    },
    {
      id: 'deaf-hard-hearing',
      name: t('accessibility:deafHardHearing'),
      description: t('accessibility:deafHardHearingDesc'),
      settings: {
        audioDescriptions: false,
        soundFeedback: false,
        screenReaderMode: false,
        enhancedFocus: true,
        skipLinks: true
      }
    }
  ]

  // Filter options by category and search
  const filteredOptions = options.filter(option => {
    const matchesCategory = activeCategory === 'all' || option.category === activeCategory
    const matchesSearch = !searchQuery.trim() || 
      option.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      option.description.toLowerCase().includes(searchQuery.toLowerCase())
    
    return matchesCategory && matchesSearch
  })

  const applyPreset = async (presetId: string) => {
    setIsApplying(true)
    const preset = accessibilityPresets.find(p => p.id === presetId)
    
    if (preset) {
      // Apply all settings from the preset
      updatePreferences(preset.settings)
      
      // Apply visual changes
      Object.entries(preset.settings).forEach(([key, value]) => {
        const option = options.find(opt => opt.id.replace('-', '') === key.replace(/([A-Z])/g, '-$1').toLowerCase())
        if (option && option.onChange) {
          option.onChange(value)
        }
      })

      announceAction(t('accessibility:presetApplied', { preset: preset.name }), 'polite')
    }
    
    setIsApplying(false)
  }

  const resetToDefaults = () => {
    // Reset all preferences to defaults
    const defaultPreferences = {
      highContrast: false,
      fontSize: 16,
      zoomLevel: 100,
      reducedMotion: false,
      enhancedFocus: false,
      screenReaderMode: false,
      audioDescriptions: false,
      soundFeedback: true,
      speechRate: 1,
      keyboardNavigation: true,
      stickyKeys: false,
      mouseKeys: false,
      clickTimeout: 500,
      readingGuide: false,
      dyslexiaFont: false,
      contentPause: false,
      simplifiedUI: false,
      skipLinks: true,
      landmarkNavigation: true,
      headingNavigation: true,
      autoSave: true
    }

    updatePreferences(defaultPreferences)
    
    // Remove all accessibility classes
    document.documentElement.classList.remove(
      'enhanced-focus',
      'keyboard-navigation', 
      'reading-guide',
      'dyslexia-font',
      'simplified-ui',
      'show-skip-links'
    )
    
    // Reset styles
    document.documentElement.style.fontSize = '16px'
    document.body.style.zoom = '100%'
    
    setTheme('system')
    disableHighContrast()
    disableReducedMotion()
    disableScreenReader()
    
    announceAction(t('accessibility:settingsReset'), 'polite')
  }

  const exportSettings = () => {
    const settings = {
      preferences,
      theme,
      direction,
      timestamp: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'accessibility-settings.json'
    a.click()
    URL.revokeObjectURL(url)
    
    announceAction(t('accessibility:settingsExported'), 'polite')
  }

  const renderOption = (option: AccessibilityOption) => {
    const Icon = option.icon

    return (
      <div key={option.id} className="p-4 border border-border rounded-lg">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
              <Icon className="w-4 h-4 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium flex items-center space-x-2">
                <span>{option.title}</span>
                {option.premium && (
                  <Crown className="w-3 h-3 text-yellow-500" />
                )}
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                {option.description}
              </p>
              {option.shortcut && (
                <div className="flex items-center space-x-1 mt-2">
                  {option.shortcut.map((key, i) => (
                    <kbd
                      key={i}
                      className="px-1.5 py-0.5 text-xs bg-muted border border-border rounded"
                    >
                      {key}
                    </kbd>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          {option.type === 'toggle' && (
            <div className="flex items-center justify-between">
              <span className="text-sm">
                {option.value ? t('accessibility:enabled') : t('accessibility:disabled')}
              </span>
              <button
                onClick={() => option.onChange?.(!option.value)}
                className={cn(
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible-ring',
                  option.value ? 'bg-primary' : 'bg-muted'
                )}
                role="switch"
                aria-checked={option.value}
              >
                <span
                  className={cn(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    option.value ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
              </button>
            </div>
          )}

          {option.type === 'slider' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">
                  {option.value}{option.unit}
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      const newValue = Math.max(option.min || 0, (option.value || 0) - (option.step || 1))
                      option.onChange?.(newValue)
                    }}
                    className="p-1 rounded hover:bg-muted focus-visible-ring"
                    aria-label={t('accessibility:decrease')}
                  >
                    <Minus className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => {
                      const newValue = Math.min(option.max || 100, (option.value || 0) + (option.step || 1))
                      option.onChange?.(newValue)
                    }}
                    className="p-1 rounded hover:bg-muted focus-visible-ring"
                    aria-label={t('accessibility:increase')}
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <input
                type="range"
                min={option.min}
                max={option.max}
                step={option.step}
                value={option.value}
                onChange={(e) => option.onChange?.(Number(e.target.value))}
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
          )}

          {option.type === 'select' && (
            <select
              value={option.value}
              onChange={(e) => option.onChange?.(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary"
            >
              {option.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          )}

          {option.type === 'button' && (
            <button
              onClick={option.onAction}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus-visible-ring"
            >
              {option.title}
            </button>
          )}
        </div>
      </div>
    )
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" dir={direction}>
      <div className="flex justify-center items-start pt-8 pb-8 px-4 min-h-full">
        <div
          ref={containerRef}
          className={cn(
            'w-full max-w-4xl bg-background border border-border rounded-xl shadow-2xl overflow-hidden',
            'animate-in fade-in-0 zoom-in-95 duration-200',
            className
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div>
              <h2 className="text-xl font-semibold flex items-center space-x-2">
                <Accessibility className="w-5 h-5 text-primary" />
                <span>{t('accessibility:accessibilityMenu')}</span>
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {t('accessibility:menuDescription')}
              </p>
            </div>
            <button
              onClick={() => onOpenChange(false)}
              className="p-2 rounded-lg hover:bg-muted focus-visible-ring"
              aria-label={t('accessibility:close')}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex h-[600px]">
            {/* Sidebar */}
            <div className="w-64 border-e border-border bg-muted/30 p-4">
              {/* Search */}
              <div className="relative mb-4">
                <Search className="absolute start-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('accessibility:searchOptions')}
                  className="w-full ps-10 pe-4 py-2 bg-background rounded-lg border border-border focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              {/* Categories */}
              <div className="space-y-1 mb-6">
                <button
                  onClick={() => setActiveCategory('all')}
                  className={cn(
                    'w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-start transition-colors focus-visible-ring',
                    activeCategory === 'all'
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  <Settings className="w-4 h-4" />
                  <span className="text-sm font-medium">{t('accessibility:allOptions')}</span>
                </button>
                {categories.map((category) => {
                  const Icon = category.icon
                  return (
                    <button
                      key={category.id}
                      onClick={() => setActiveCategory(category.id)}
                      className={cn(
                        'w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-start transition-colors focus-visible-ring',
                        activeCategory === category.id
                          ? 'bg-primary text-primary-foreground'
                          : 'hover:bg-muted'
                      )}
                      title={category.description}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="text-sm font-medium">{category.label}</span>
                    </button>
                  )
                })}
              </div>

              {/* Quick actions */}
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-muted-foreground">
                  {t('accessibility:quickActions')}
                </h3>
                <button
                  onClick={resetToDefaults}
                  className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-muted focus-visible-ring text-start"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span className="text-sm">{t('accessibility:resetDefaults')}</span>
                </button>
                <button
                  onClick={exportSettings}
                  className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-muted focus-visible-ring text-start"
                >
                  <Download className="w-4 h-4" />
                  <span className="text-sm">{t('accessibility:exportSettings')}</span>
                </button>
              </div>
            </div>

            {/* Main content */}
            <div className="flex-1 overflow-y-auto">
              {/* Presets section */}
              {activeCategory === 'all' && (
                <div className="p-6 border-b border-border">
                  <h3 className="text-lg font-semibold mb-4">
                    {t('accessibility:accessibilityPresets')}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {accessibilityPresets.map((preset) => (
                      <div key={preset.id} className="p-4 border border-border rounded-lg">
                        <h4 className="font-medium mb-2">{preset.name}</h4>
                        <p className="text-sm text-muted-foreground mb-3">
                          {preset.description}
                        </p>
                        <button
                          onClick={() => applyPreset(preset.id)}
                          disabled={isApplying}
                          className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus-visible-ring disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isApplying ? (
                            <div className="flex items-center justify-center space-x-2">
                              <RefreshCw className="w-4 h-4 animate-spin" />
                              <span>{t('accessibility:applying')}</span>
                            </div>
                          ) : (
                            t('accessibility:applyPreset')
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Options */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold">
                    {activeCategory === 'all' 
                      ? t('accessibility:allOptions')
                      : categories.find(c => c.id === activeCategory)?.label
                    }
                  </h3>
                  <span className="text-sm text-muted-foreground">
                    {filteredOptions.length} {t('accessibility:optionsFound')}
                  </span>
                </div>

                {filteredOptions.length > 0 ? (
                  <div className="grid gap-4">
                    {filteredOptions.map(renderOption)}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                      <Search className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">
                      {t('accessibility:noOptionsFound')}
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      {searchQuery.trim() 
                        ? t('accessibility:noResultsForQuery', { query: searchQuery })
                        : t('accessibility:noOptionsInCategory')
                      }
                    </p>
                    <button
                      onClick={() => {
                        setSearchQuery('')
                        setActiveCategory('all')
                      }}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 focus-visible-ring"
                    >
                      {t('accessibility:showAllOptions')}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-border bg-muted/30">
            <div className="text-sm text-muted-foreground">
              {t('accessibility:keyboardTip')}
            </div>
            <div className="flex items-center space-x-2">
              <Link
                href="/accessibility"
                className="text-sm text-primary hover:text-primary/80 focus-visible-ring rounded"
              >
                {t('accessibility:learnMore')}
              </Link>
              <span className="text-muted-foreground">•</span>
              <Link
                href="/support"
                className="text-sm text-primary hover:text-primary/80 focus-visible-ring rounded"
              >
                {t('accessibility:getHelp')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}