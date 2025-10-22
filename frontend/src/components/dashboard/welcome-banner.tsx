import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useTranslation } from 'next-i18next'
import { useRouter } from 'next/router'
import {
  Sparkles,
  Brain,
  Zap,
  Star,
  ArrowRight,
  X,
  Gift,
  Crown,
  Rocket,
  Target,
  TrendingUp,
  Users,
  FileText,
  MessageSquare,
  Upload,
  Search,
  Bookmark,
  Settings,
  HelpCircle,
  Award,
  Trophy,
  Medal,
  Heart,
  ThumbsUp,
  Share2,
  Eye,
  Clock,
  Calendar,
  Bell,
  Mail,
  Phone,
  Globe,
  MapPin,
  Navigation,
  Compass,
  Map,
  Route,
  Plane,
  Car,
  Truck,
  Bus,
  Train,
  Ship,
  Anchor,
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
  CloudRain,
  Umbrella,
  Wind,
  Thermometer
} from '@/lib/icon-mappings'
import Image from 'next/image'

// Hooks
import { useAccessibility } from '@/components/providers/accessibility-provider'
import { useRTL } from '@/components/providers/rtl-provider'

// Utils
import { cn } from '@/lib/utils'

interface WelcomeBannerProps {
  className?: string
  variant?: 'default' | 'compact' | 'hero'
  showDismiss?: boolean
  showActions?: boolean
}

interface QuickAction {
  id: string
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  href: string
  color: 'primary' | 'secondary' | 'success' | 'warning'
}

interface Achievement {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  unlocked: boolean
  progress?: number
  target?: number
}

export function WelcomeBanner({
  className,
  variant = 'default',
  showDismiss = true,
  showActions = true
}: WelcomeBannerProps) {
  const { data: session } = useSession()
  const { t } = useTranslation(['dashboard', 'common'])
  const router = useRouter()
  const { direction } = useRTL()
  const { announceAction } = useAccessibility()

  const [isDismissed, setIsDismissed] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [showAchievements, setShowAchievements] = useState(false)

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  // Check if banner was previously dismissed
  useEffect(() => {
    const dismissed = localStorage.getItem('welcome-banner-dismissed')
    if (dismissed === 'true') {
      setIsDismissed(true)
    }
  }, [])

  const quickActions: QuickAction[] = [
    {
      id: 'upload',
      label: t('dashboard:uploadFirst'),
      description: t('dashboard:uploadFirstDesc'),
      icon: Upload,
      href: '/upload',
      color: 'primary'
    },
    {
      id: 'chat',
      label: t('dashboard:tryAI'),
      description: t('dashboard:tryAIDesc'),
      icon: Brain,
      href: '/chat',
      color: 'secondary'
    },
    {
      id: 'explore',
      label: t('dashboard:exploreFeatures'),
      description: t('dashboard:exploreFeaturesDesc'),
      icon: Sparkles,
      href: '/features',
      color: 'success'
    },
    {
      id: 'invite',
      label: t('dashboard:inviteTeam'),
      description: t('dashboard:inviteTeamDesc'),
      icon: Users,
      href: '/team/invite',
      color: 'warning'
    }
  ]

  const achievements: Achievement[] = [
    {
      id: 'first-upload',
      title: t('dashboard:firstUpload'),
      description: t('dashboard:firstUploadDesc'),
      icon: Upload,
      unlocked: true
    },
    {
      id: 'search-master',
      title: t('dashboard:searchMaster'),
      description: t('dashboard:searchMasterDesc'),
      icon: Search,
      unlocked: false,
      progress: 15,
      target: 50
    },
    {
      id: 'ai-enthusiast',
      title: t('dashboard:aiEnthusiast'),
      description: t('dashboard:aiEnthusiastDesc'),
      icon: Brain,
      unlocked: false,
      progress: 8,
      target: 25
    },
    {
      id: 'collaborator',
      title: t('dashboard:collaborator'),
      description: t('dashboard:collaboratorDesc'),
      icon: Users,
      unlocked: false,
      progress: 2,
      target: 10
    }
  ]

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = currentTime.getHours()
    
    if (hour < 12) {
      return t('dashboard:goodMorning')
    } else if (hour < 18) {
      return t('dashboard:goodAfternoon')
    } else {
      return t('dashboard:goodEvening')
    }
  }

  // Get appropriate icon based on time
  const getTimeIcon = () => {
    const hour = currentTime.getHours()
    
    if (hour >= 6 && hour < 12) {
      return Sun
    } else if (hour >= 12 && hour < 18) {
      return Sun
    } else {
      return Moon
    }
  }

  const handleDismiss = () => {
    setIsDismissed(true)
    localStorage.setItem('welcome-banner-dismissed', 'true')
    announceAction(t('dashboard:bannerDismissed'), 'polite')
  }

  const handleActionClick = (action: QuickAction) => {
    router.push(action.href)
    announceAction(t('dashboard:actionTriggered', { action: action.label }), 'polite')
  }

  const getActionColor = (color: QuickAction['color']) => {
    switch (color) {
      case 'primary':
        return 'bg-primary text-primary-foreground hover:bg-primary/90'
      case 'secondary':
        return 'bg-secondary text-secondary-foreground hover:bg-secondary/90'
      case 'success':
        return 'bg-green-500 text-white hover:bg-green-600'
      case 'warning':
        return 'bg-yellow-500 text-white hover:bg-yellow-600'
    }
  }

  if (isDismissed) {
    return null
  }

  if (variant === 'compact') {
    return (
      <div 
        className={cn(
          'relative p-4 bg-gradient-to-r from-primary/10 to-secondary/10 rounded-lg border border-border',
          className
        )}
        dir={direction}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold">
                {getGreeting()}, {session?.user?.name?.split(' ')[0] || t('dashboard:user')}!
              </h3>
              <p className="text-sm text-muted-foreground">
                {t('dashboard:readyToExplore')}
              </p>
            </div>
          </div>
          
          {showDismiss && (
            <button
              onClick={handleDismiss}
              className="p-1 rounded-md hover:bg-muted focus-visible-ring"
              aria-label={t('dashboard:dismissBanner')}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    )
  }

  if (variant === 'hero') {
    const TimeIcon = getTimeIcon()
    
    return (
      <div 
        className={cn(
          'relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary via-primary/90 to-secondary',
          'text-primary-foreground',
          className
        )}
        dir={direction}
      >
        {/* Background decoration */}
        <div className="absolute inset-0 bg-[url('/images/grid.svg')] opacity-10" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-32 translate-x-32" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-24 -translate-x-24" />
        
        <div className="relative p-8 lg:p-12">
          <div className="max-w-4xl">
            {/* Header */}
            <div className="flex items-center space-x-3 mb-6">
              <TimeIcon className="w-8 h-8" />
              <div>
                <h1 className="text-3xl lg:text-4xl font-bold">
                  {getGreeting()}, {session?.user?.name?.split(' ')[0] || t('dashboard:user')}!
                </h1>
                <p className="text-lg text-primary-foreground/80">
                  {t('dashboard:heroSubtitle')}
                </p>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="text-center">
                <div className="text-2xl font-bold">1,247</div>
                <div className="text-sm text-primary-foreground/70">{t('dashboard:documents')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">156</div>
                <div className="text-sm text-primary-foreground/70">{t('dashboard:searchesToday')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">89</div>
                <div className="text-sm text-primary-foreground/70">{t('dashboard:aiQueries')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">24</div>
                <div className="text-sm text-primary-foreground/70">{t('dashboard:activeUsers')}</div>
              </div>
            </div>

            {/* Actions */}
            {showActions && (
              <div className="flex flex-wrap gap-4">
                {quickActions.slice(0, 2).map((action) => {
                  const Icon = action.icon
                  return (
                    <button
                      key={action.id}
                      onClick={() => handleActionClick(action)}
                      className="flex items-center space-x-2 px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg backdrop-blur-sm transition-colors focus-visible-ring"
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{action.label}</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Dismiss button */}
          {showDismiss && (
            <button
              onClick={handleDismiss}
              className="absolute top-4 end-4 p-2 rounded-lg hover:bg-white/10 focus-visible-ring"
              aria-label={t('dashboard:dismissBanner')}
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    )
  }

  // Default variant
  const TimeIcon = getTimeIcon()
  
  return (
    <div 
      className={cn(
        'relative overflow-hidden rounded-xl bg-gradient-to-r from-primary/5 via-secondary/5 to-primary/5',
        'border border-border',
        className
      )}
      dir={direction}
    >
      {/* Background pattern */}
      <div className="absolute inset-0 bg-[url('/images/dots.svg')] opacity-5" />
      
      <div className="relative p-6 lg:p-8">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center space-y-6 lg:space-y-0">
          {/* Welcome content */}
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
              <TimeIcon className="w-6 h-6 text-primary" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">
                {getGreeting()}, {session?.user?.name?.split(' ')[0] || t('dashboard:user')}!
              </h2>
              <p className="text-muted-foreground">
                {t('dashboard:welcomeMessage')}
              </p>
              
              {/* Achievement preview */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowAchievements(!showAchievements)}
                  className="flex items-center space-x-2 text-sm text-primary hover:text-primary/80 focus-visible-ring rounded"
                >
                  <Award className="w-4 h-4" />
                  <span>{t('dashboard:achievements')}</span>
                  <span className="bg-primary/10 text-primary px-2 py-0.5 rounded-full text-xs">
                    {achievements.filter(a => a.unlocked).length}/{achievements.length}
                  </span>
                </button>
              </div>

              {/* Achievements dropdown */}
              {showAchievements && (
                <div className="mt-4 p-4 bg-background border border-border rounded-lg shadow-lg">
                  <h3 className="font-semibold mb-3">{t('dashboard:yourAchievements')}</h3>
                  <div className="space-y-3">
                    {achievements.map((achievement) => {
                      const Icon = achievement.icon
                      return (
                        <div key={achievement.id} className="flex items-center space-x-3">
                          <div className={cn(
                            'w-8 h-8 rounded-lg flex items-center justify-center',
                            achievement.unlocked 
                              ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400'
                              : 'bg-muted text-muted-foreground'
                          )}>
                            <Icon className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium">{achievement.title}</p>
                            <p className="text-xs text-muted-foreground">{achievement.description}</p>
                            {!achievement.unlocked && achievement.progress && achievement.target && (
                              <div className="mt-1">
                                <div className="w-full bg-muted rounded-full h-1.5">
                                  <div 
                                    className="bg-primary h-1.5 rounded-full transition-all duration-300"
                                    style={{ width: `${(achievement.progress / achievement.target) * 100}%` }}
                                  />
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {achievement.progress}/{achievement.target}
                                </p>
                              </div>
                            )}
                          </div>
                          {achievement.unlocked && (
                            <Trophy className="w-4 h-4 text-yellow-500" />
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Quick actions */}
          {showActions && (
            <div className="flex flex-col sm:flex-row gap-3">
              {quickActions.slice(0, 3).map((action) => {
                const Icon = action.icon
                return (
                  <button
                    key={action.id}
                    onClick={() => handleActionClick(action)}
                    className={cn(
                      'flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors focus-visible-ring',
                      getActionColor(action.color)
                    )}
                    title={action.description}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="whitespace-nowrap">{action.label}</span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Tips section */}
        <div className="mt-6 p-4 bg-muted/50 rounded-lg border border-border/50">
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
              <Zap className="w-3 h-3 text-blue-600" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-medium mb-1">{t('dashboard:tipOfTheDay')}</h4>
              <p className="text-sm text-muted-foreground">
                {t('dashboard:tipContent')}
              </p>
            </div>
          </div>
        </div>

        {/* Dismiss button */}
        {showDismiss && (
          <button
            onClick={handleDismiss}
            className="absolute top-4 end-4 p-2 rounded-lg hover:bg-muted focus-visible-ring"
            aria-label={t('dashboard:dismissBanner')}
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}