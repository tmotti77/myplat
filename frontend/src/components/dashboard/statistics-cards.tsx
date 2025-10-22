import { useState, useEffect } from 'react'
import { useTranslation } from 'next-i18next'
import {
  FileText,
  Users,
  MessageSquare,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Activity,
  Clock,
  Eye,
  Download,
  Upload,
  Star,
  Heart,
  Share2,
  Bookmark,
  Search,
  Brain,
  Zap,
  Database,
  Server,
  Cloud,
  Shield,
  Award,
  Trophy,
  Target,
  Flame,
  Lightning,
  Sparkles,
  ArrowUp,
  ArrowDown,
  Minus,
  Plus,
  MoreHorizontal,
  ExternalLink,
  RefreshCw,
  Info,
  AlertCircle,
  CheckCircle,
  XCircle,
  HelpCircle,
  Calendar,
  Filter,
  SlidersHorizontal,
  Settings,
  Maximize2,
  Minimize2,
  RotateCcw,
  Timer,
  Gauge,
  Percent,
  Hash,
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
  TrendingUpIcon,
  TrendingDownIcon
} from '@/lib/icon-mappings'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface StatisticsCardsProps {
  className?: string
  variant?: 'default' | 'compact' | 'detailed'
  showTrends?: boolean
  showComparisons?: boolean
  timeRange?: '24h' | '7d' | '30d' | '90d' | '1y'
  onTimeRangeChange?: (range: string) => void
}

interface Statistic {
  id: string
  label: string
  value: string | number
  previousValue?: string | number
  change?: number
  changeType?: 'increase' | 'decrease' | 'neutral'
  icon: React.ComponentType<{ className?: string }>
  description?: string
  trend?: Array<{ date: string; value: number }>
  target?: number
  unit?: string
  format?: 'number' | 'percentage' | 'currency' | 'duration' | 'bytes'
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'destructive' | 'info'
  category: 'content' | 'usage' | 'performance' | 'engagement' | 'financial'
  premium?: boolean
  clickable?: boolean
  href?: string
}

export function StatisticsCards({
  className,
  variant = 'default',
  showTrends = true,
  showComparisons = true,
  timeRange = '30d',
  onTimeRangeChange
}: StatisticsCardsProps) {
  const { t } = useTranslation(['dashboard', 'common'])
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [isLoading, setIsLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // Mock statistics data - replace with actual API calls
  const statistics: Statistic[] = [
    // Content statistics
    {
      id: 'total-documents',
      label: t('dashboard:totalDocuments'),
      value: 1247,
      previousValue: 1189,
      change: 4.9,
      changeType: 'increase',
      icon: FileText,
      description: t('dashboard:totalDocumentsDesc'),
      category: 'content',
      format: 'number',
      color: 'primary',
      clickable: true,
      href: '/documents',
      trend: [
        { date: '2024-01-01', value: 980 },
        { date: '2024-01-08', value: 1020 },
        { date: '2024-01-15', value: 1050 },
        { date: '2024-01-22', value: 1120 },
        { date: '2024-01-29', value: 1189 },
        { date: '2024-02-05', value: 1247 }
      ]
    },
    {
      id: 'storage-used',
      label: t('dashboard:storageUsed'),
      value: 15.6,
      previousValue: 14.2,
      change: 9.9,
      changeType: 'increase',
      icon: Database,
      description: t('dashboard:storageUsedDesc'),
      category: 'content',
      format: 'bytes',
      unit: 'GB',
      color: 'warning',
      target: 50
    },
    {
      id: 'collections',
      label: t('dashboard:collections'),
      value: 32,
      previousValue: 28,
      change: 14.3,
      changeType: 'increase',
      icon: Bookmark,
      description: t('dashboard:collectionsDesc'),
      category: 'content',
      format: 'number',
      color: 'success',
      clickable: true,
      href: '/collections'
    },

    // Usage statistics
    {
      id: 'searches-today',
      label: t('dashboard:searchesToday'),
      value: 156,
      previousValue: 134,
      change: 16.4,
      changeType: 'increase',
      icon: Search,
      description: t('dashboard:searchesTodayDesc'),
      category: 'usage',
      format: 'number',
      color: 'info'
    },
    {
      id: 'ai-queries',
      label: t('dashboard:aiQueries'),
      value: 89,
      previousValue: 76,
      change: 17.1,
      changeType: 'increase',
      icon: Brain,
      description: t('dashboard:aiQueriesDesc'),
      category: 'usage',
      format: 'number',
      color: 'primary',
      premium: true
    },
    {
      id: 'downloads',
      label: t('dashboard:downloads'),
      value: 234,
      previousValue: 198,
      change: 18.2,
      changeType: 'increase',
      icon: Download,
      description: t('dashboard:downloadsDesc'),
      category: 'usage',
      format: 'number',
      color: 'secondary'
    },

    // Performance statistics
    {
      id: 'avg-response-time',
      label: t('dashboard:avgResponseTime'),
      value: 1.2,
      previousValue: 1.5,
      change: -20.0,
      changeType: 'decrease',
      icon: Zap,
      description: t('dashboard:avgResponseTimeDesc'),
      category: 'performance',
      format: 'duration',
      unit: 's',
      color: 'success'
    },
    {
      id: 'uptime',
      label: t('dashboard:uptime'),
      value: 99.9,
      previousValue: 99.7,
      change: 0.2,
      changeType: 'increase',
      icon: Activity,
      description: t('dashboard:uptimeDesc'),
      category: 'performance',
      format: 'percentage',
      color: 'success'
    },
    {
      id: 'cache-hit-rate',
      label: t('dashboard:cacheHitRate'),
      value: 85.3,
      previousValue: 82.1,
      change: 3.9,
      changeType: 'increase',
      icon: Gauge,
      description: t('dashboard:cacheHitRateDesc'),
      category: 'performance',
      format: 'percentage',
      color: 'info'
    },

    // Engagement statistics
    {
      id: 'active-users',
      label: t('dashboard:activeUsers'),
      value: 24,
      previousValue: 21,
      change: 14.3,
      changeType: 'increase',
      icon: Users,
      description: t('dashboard:activeUsersDesc'),
      category: 'engagement',
      format: 'number',
      color: 'primary',
      clickable: true,
      href: '/team'
    },
    {
      id: 'collaboration-sessions',
      label: t('dashboard:collaborationSessions'),
      value: 67,
      previousValue: 52,
      change: 28.8,
      changeType: 'increase',
      icon: Share2,
      description: t('dashboard:collaborationSessionsDesc'),
      category: 'engagement',
      format: 'number',
      color: 'secondary'
    },
    {
      id: 'feedback-score',
      label: t('dashboard:feedbackScore'),
      value: 4.7,
      previousValue: 4.5,
      change: 4.4,
      changeType: 'increase',
      icon: Star,
      description: t('dashboard:feedbackScoreDesc'),
      category: 'engagement',
      format: 'number',
      unit: '/5',
      color: 'warning'
    },

    // Financial statistics (premium)
    {
      id: 'cost-savings',
      label: t('dashboard:costSavings'),
      value: 1250,
      previousValue: 980,
      change: 27.6,
      changeType: 'increase',
      icon: DollarSign,
      description: t('dashboard:costSavingsDesc'),
      category: 'financial',
      format: 'currency',
      color: 'success',
      premium: true
    },
    {
      id: 'efficiency-gain',
      label: t('dashboard:efficiencyGain'),
      value: 35.2,
      previousValue: 28.7,
      change: 22.6,
      changeType: 'increase',
      icon: TrendingUp,
      description: t('dashboard:efficiencyGainDesc'),
      category: 'financial',
      format: 'percentage',
      color: 'success',
      premium: true
    }
  ]

  const categories = [
    { id: 'all', label: t('dashboard:allMetrics'), icon: BarChart3 },
    { id: 'content', label: t('dashboard:content'), icon: FileText },
    { id: 'usage', label: t('dashboard:usage'), icon: Activity },
    { id: 'performance', label: t('dashboard:performance'), icon: Zap },
    { id: 'engagement', label: t('dashboard:engagement'), icon: Users },
    { id: 'financial', label: t('dashboard:financial'), icon: DollarSign }
  ]

  const timeRanges = [
    { value: '24h', label: t('dashboard:last24Hours') },
    { value: '7d', label: t('dashboard:last7Days') },
    { value: '30d', label: t('dashboard:last30Days') },
    { value: '90d', label: t('dashboard:last90Days') },
    { value: '1y', label: t('dashboard:lastYear') }
  ]

  const filteredStatistics = selectedCategory === 'all' 
    ? statistics 
    : statistics.filter(stat => stat.category === selectedCategory)

  // Refresh data
  const handleRefresh = async () => {
    setIsLoading(true)
    announceAction(t('dashboard:refreshingData'), 'polite')
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    setIsLoading(false)
    announceAction(t('dashboard:dataRefreshed'), 'polite')
  }

  // Format values based on type
  const formatValue = (stat: Statistic) => {
    const value = typeof stat.value === 'string' ? parseFloat(stat.value) : stat.value

    switch (stat.format) {
      case 'percentage':
        return `${value.toFixed(1)}%`
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(value)
      case 'duration':
        return `${value.toFixed(1)}${stat.unit || 's'}`
      case 'bytes':
        return `${value.toFixed(1)} ${stat.unit || 'GB'}`
      case 'number':
        return value >= 1000 
          ? `${(value / 1000).toFixed(1)}K` 
          : value.toString()
      default:
        return `${value}${stat.unit || ''}`
    }
  }

  // Get change indicator
  const getChangeIndicator = (stat: Statistic) => {
    if (!stat.change) return null

    const isPositive = stat.changeType === 'increase'
    const isNegative = stat.changeType === 'decrease'
    
    const changeColor = isPositive ? 'text-green-600' : 
                       isNegative ? 'text-red-600' : 'text-muted-foreground'
    
    const ChangeIcon = isPositive ? ArrowUp : isNegative ? ArrowDown : Minus

    return (
      <div className={cn('flex items-center space-x-1 text-xs', changeColor)}>
        <ChangeIcon className="w-3 h-3" />
        <span>{Math.abs(stat.change).toFixed(1)}%</span>
      </div>
    )
  }

  // Get card color classes
  const getCardColor = (color?: Statistic['color']) => {
    switch (color) {
      case 'primary':
        return 'border-primary/20 bg-primary/5'
      case 'secondary':
        return 'border-secondary/20 bg-secondary/5'
      case 'success':
        return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950'
      case 'destructive':
        return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950'
      case 'info':
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950'
      default:
        return 'border-border bg-card'
    }
  }

  if (variant === 'compact') {
    return (
      <div className={cn('grid grid-cols-2 md:grid-cols-4 gap-4', className)} dir={direction}>
        {filteredStatistics.slice(0, 4).map((stat) => {
          const Icon = stat.icon
          return (
            <div
              key={stat.id}
              className={cn(
                'p-4 rounded-lg border transition-colors',
                getCardColor(stat.color),
                stat.clickable && 'hover:shadow-md cursor-pointer'
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-5 h-5 text-muted-foreground" />
                {getChangeIndicator(stat)}
              </div>
              <div>
                <p className="text-2xl font-bold">{formatValue(stat)}</p>
                <p className="text-sm text-muted-foreground truncate">{stat.label}</p>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn('space-y-6', className)} dir={direction}>
      {/* Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
        {/* Category filter */}
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => {
            const Icon = category.icon
            return (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={cn(
                  'flex items-center space-x-2 px-3 py-2 rounded-lg border transition-colors focus-visible-ring',
                  selectedCategory === category.id
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background text-muted-foreground border-border hover:bg-muted hover:text-foreground'
                )}
                aria-pressed={selectedCategory === category.id}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{category.label}</span>
              </button>
            )
          })}
        </div>

        {/* Time range and controls */}
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => onTimeRangeChange?.(e.target.value)}
            className="px-3 py-2 text-sm bg-background border border-border rounded-lg focus:border-primary focus:ring-1 focus:ring-primary"
          >
            {timeRanges.map((range) => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
          
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2 rounded-lg border border-border hover:bg-muted focus-visible-ring disabled:opacity-50"
            aria-label={t('dashboard:refreshData')}
          >
            <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
          </button>
        </div>
      </div>

      {/* Statistics Grid */}
      <div className={cn(
        'grid gap-6',
        variant === 'detailed' 
          ? 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3'
          : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
      )}>
        {filteredStatistics.map((stat) => {
          const Icon = stat.icon
          
          return (
            <div
              key={stat.id}
              className={cn(
                'group relative p-6 rounded-xl border transition-all duration-200',
                getCardColor(stat.color),
                stat.clickable && 'hover:shadow-lg hover:scale-[1.02] cursor-pointer',
                stat.premium && 'ring-1 ring-yellow-200 dark:ring-yellow-800'
              )}
              onClick={stat.clickable && stat.href ? () => window.location.href = stat.href : undefined}
            >
              {/* Premium badge */}
              {stat.premium && (
                <div className="absolute top-3 end-3">
                  <div className="flex items-center space-x-1 px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">
                    <Sparkles className="w-3 h-3" />
                    <span>Pro</span>
                  </div>
                </div>
              )}

              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className={cn(
                  'p-3 rounded-lg',
                  stat.color === 'primary' && 'bg-primary/20 text-primary',
                  stat.color === 'secondary' && 'bg-secondary/20 text-secondary-foreground',
                  stat.color === 'success' && 'bg-green-200 text-green-700 dark:bg-green-800 dark:text-green-300',
                  stat.color === 'warning' && 'bg-yellow-200 text-yellow-700 dark:bg-yellow-800 dark:text-yellow-300',
                  stat.color === 'destructive' && 'bg-red-200 text-red-700 dark:bg-red-800 dark:text-red-300',
                  stat.color === 'info' && 'bg-blue-200 text-blue-700 dark:bg-blue-800 dark:text-blue-300',
                  !stat.color && 'bg-muted text-muted-foreground'
                )}>
                  <Icon className="w-6 h-6" />
                </div>

                {stat.clickable && (
                  <ExternalLink className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
              </div>

              {/* Content */}
              <div className="space-y-2">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-3xl font-bold">{formatValue(stat)}</p>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                  </div>
                  {showComparisons && getChangeIndicator(stat)}
                </div>

                {stat.description && variant === 'detailed' && (
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {stat.description}
                  </p>
                )}

                {/* Progress bar for targets */}
                {stat.target && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{t('dashboard:target')}</span>
                      <span>{stat.format === 'percentage' ? `${stat.target}%` : stat.target}</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className={cn(
                          'h-2 rounded-full transition-all duration-300',
                          stat.color === 'success' && 'bg-green-500',
                          stat.color === 'warning' && 'bg-yellow-500',
                          stat.color === 'primary' && 'bg-primary',
                          !stat.color && 'bg-blue-500'
                        )}
                        style={{ 
                          width: `${Math.min(100, ((typeof stat.value === 'number' ? stat.value : parseFloat(stat.value)) / stat.target) * 100)}%` 
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Mini trend chart */}
                {showTrends && stat.trend && variant === 'detailed' && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                      <span>{t('dashboard:trend')}</span>
                      <span>{timeRange}</span>
                    </div>
                    <div className="h-12 flex items-end space-x-1">
                      {stat.trend.map((point, index) => {
                        const maxValue = Math.max(...stat.trend!.map(p => p.value))
                        const height = (point.value / maxValue) * 100
                        return (
                          <div
                            key={index}
                            className={cn(
                              'flex-1 rounded-t transition-all duration-300',
                              stat.color === 'success' && 'bg-green-200 dark:bg-green-800',
                              stat.color === 'warning' && 'bg-yellow-200 dark:bg-yellow-800',
                              stat.color === 'primary' && 'bg-primary/20',
                              !stat.color && 'bg-blue-200 dark:bg-blue-800'
                            )}
                            style={{ height: `${height}%` }}
                            title={`${point.date}: ${point.value}`}
                          />
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Empty state */}
      {filteredStatistics.length === 0 && (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {t('dashboard:noStatisticsFound')}
          </h3>
          <p className="text-muted-foreground mb-4">
            {t('dashboard:noStatisticsDescription')}
          </p>
          <button
            onClick={() => setSelectedCategory('all')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 focus-visible-ring"
          >
            {t('dashboard:showAllMetrics')}
          </button>
        </div>
      )}
    </div>
  )
}