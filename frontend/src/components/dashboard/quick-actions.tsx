import { useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import {
  Upload,
  MessageSquare,
  FileText,
  Users,
  Settings,
  HelpCircle,
  Plus,
  Search,
  Brain,
  Star,
  Archive,
  Share2,
  Download,
  Eye,
  Edit,
  Copy,
  Trash2,
  Filter,
  Calendar,
  Clock,
  TrendingUp,
  BarChart3,
  Activity,
  Database,
  Shield,
  Lock,
  UserPlus,
  Mail,
  Globe,
  Camera,
  Video,
  Music as MusicIcon,
  Image,
  Folder,
  FolderPlus,
  File,
  FileImage,
  FileVideo,
  FileAudio,
  Bookmark,
  Tag,
  Lightbulb,
  Rocket,
  Target,
  Zap as ZapIcon
} from 'lucide-react'

interface QuickAction {
  id: string
  title: string
  description: string
  icon: React.ComponentType<any>
  href?: string
  action?: () => void
  color: string
  category: string
  popular?: boolean
}

const QuickActions = () => {
  const router = useRouter()
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const quickActions: QuickAction[] = [
    // Document Actions
    {
      id: 'upload-document',
      title: 'Upload Document',
      description: 'Add new documents to your knowledge base',
      icon: Upload,
      href: '/documents/upload',
      color: 'bg-blue-500',
      category: 'documents',
      popular: true
    },
    {
      id: 'browse-documents',
      title: 'Browse Documents',
      description: 'View and manage your document collection',
      icon: FileText,
      href: '/documents',
      color: 'bg-green-500',
      category: 'documents',
      popular: true
    },
    {
      id: 'search-documents',
      title: 'Search Documents',
      description: 'Find specific information in your documents',
      icon: Search,
      href: '/search',
      color: 'bg-purple-500',
      category: 'documents'
    },

    // AI & Chat Actions
    {
      id: 'start-chat',
      title: 'Start AI Chat',
      description: 'Ask questions about your documents',
      icon: MessageSquare,
      href: '/chat',
      color: 'bg-indigo-500',
      category: 'ai',
      popular: true
    },
    {
      id: 'ai-insights',
      title: 'AI Insights',
      description: 'Get intelligent analysis of your content',
      icon: Brain,
      action: () => console.log('AI Insights'),
      color: 'bg-pink-500',
      category: 'ai'
    },
    {
      id: 'smart-summaries',
      title: 'Smart Summaries',
      description: 'Generate automatic summaries',
      icon: Lightbulb,
      action: () => console.log('Smart Summaries'),
      color: 'bg-yellow-500',
      category: 'ai'
    },

    // Organization Actions
    {
      id: 'create-collection',
      title: 'Create Collection',
      description: 'Organize documents into collections',
      icon: FolderPlus,
      action: () => console.log('Create Collection'),
      color: 'bg-emerald-500',
      category: 'organization'
    },
    {
      id: 'add-tags',
      title: 'Manage Tags',
      description: 'Tag and categorize your content',
      icon: Tag,
      action: () => console.log('Manage Tags'),
      color: 'bg-orange-500',
      category: 'organization'
    },
    {
      id: 'bookmarks',
      title: 'Bookmarks',
      description: 'Access your saved items',
      icon: Bookmark,
      href: '/bookmarks',
      color: 'bg-red-500',
      category: 'organization'
    },

    // Analytics Actions
    {
      id: 'view-analytics',
      title: 'View Analytics',
      description: 'See your usage statistics',
      icon: BarChart3,
      href: '/analytics',
      color: 'bg-cyan-500',
      category: 'analytics'
    },
    {
      id: 'activity-log',
      title: 'Activity Log',
      description: 'Review your recent activity',
      icon: Activity,
      href: '/activity',
      color: 'bg-teal-500',
      category: 'analytics'
    },
    {
      id: 'performance',
      title: 'Performance',
      description: 'Monitor system performance',
      icon: TrendingUp,
      action: () => console.log('Performance'),
      color: 'bg-violet-500',
      category: 'analytics'
    },

    // Settings Actions
    {
      id: 'account-settings',
      title: 'Account Settings',
      description: 'Manage your account preferences',
      icon: Settings,
      href: '/settings',
      color: 'bg-gray-500',
      category: 'settings'
    },
    {
      id: 'user-management',
      title: 'User Management',
      description: 'Manage team members and permissions',
      icon: Users,
      href: '/users',
      color: 'bg-blue-600',
      category: 'settings'
    },
    {
      id: 'security',
      title: 'Security',
      description: 'Configure security settings',
      icon: Shield,
      href: '/security',
      color: 'bg-red-600',
      category: 'settings'
    }
  ]

  const categories = [
    { id: 'all', name: 'All Actions', icon: Grid3X3 },
    { id: 'documents', name: 'Documents', icon: FileText },
    { id: 'ai', name: 'AI & Chat', icon: Brain },
    { id: 'organization', name: 'Organization', icon: Folder },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
    { id: 'settings', name: 'Settings', icon: Settings }
  ]

  const filteredActions = quickActions.filter(action => {
    const matchesCategory = selectedCategory === 'all' || action.category === selectedCategory
    const matchesSearch = action.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         action.description.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const popularActions = quickActions.filter(action => action.popular)

  const handleActionClick = (action: QuickAction) => {
    if (action.href) {
      router.push(action.href)
    } else if (action.action) {
      action.action()
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Quick Actions
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Shortcuts to common tasks and features
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
            <Filter className="w-4 h-4" />
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative mb-6">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Search actions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Popular Actions */}
      {selectedCategory === 'all' && searchTerm === '' && (
        <div className="mb-8">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center">
            <Star className="w-4 h-4 mr-2 text-yellow-500" />
            Popular Actions
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {popularActions.map((action) => (
              <button
                key={action.id}
                onClick={() => handleActionClick(action)}
                className="group flex items-center p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:shadow-sm transition-all duration-200 text-left bg-white dark:bg-gray-700"
              >
                <div className={`flex-shrink-0 w-8 h-8 ${action.color} rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200`}>
                  <action.icon className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {action.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {action.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Category Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`flex items-center px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              selectedCategory === category.id
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            <category.icon className="w-3 h-3 mr-1.5" />
            {category.name}
          </button>
        ))}
      </div>

      {/* Actions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredActions.map((action) => (
          <button
            key={action.id}
            onClick={() => handleActionClick(action)}
            className="group p-4 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:shadow-md transition-all duration-200 text-left bg-white dark:bg-gray-700"
          >
            <div className="flex items-start">
              <div className={`flex-shrink-0 w-10 h-10 ${action.color} rounded-lg flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-200`}>
                <action.icon className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {action.title}
                  </h4>
                  {action.popular && (
                    <Star className="w-3 h-3 text-yellow-500 fill-current" />
                  )}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                  {action.description}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {filteredActions.length === 0 && (
        <div className="text-center py-8">
          <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No actions found
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Try adjusting your search or category filter
          </p>
        </div>
      )}
    </div>
  )
}

// Add missing Grid3X3 icon import
import { Grid3X3 } from 'lucide-react'

export default QuickActions