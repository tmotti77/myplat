import Head from 'next/head'
import { useState } from 'react'

// Components
import { MainLayout } from '@/components/layouts/main-layout'
import { SearchInterface } from '@/components/search/search-interface'
import { RecentDocuments } from '@/components/documents/recent-documents'
import QuickActions from '@/components/dashboard/quick-actions'
import { StatisticsCards } from '@/components/dashboard/statistics-cards'
import { ActivityFeed } from '@/components/dashboard/activity-feed'
import { WelcomeBanner } from '@/components/dashboard/welcome-banner'

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <>
      <Head>
        <title>Dashboard | Hybrid RAG Platform</title>
        <meta 
          name="description" 
          content="AI-powered document analysis and chat platform with intelligent search capabilities" 
        />
        <meta property="og:title" content="Hybrid RAG Platform Dashboard" />
        <meta property="og:description" content="Transform your documents into intelligent conversations" />
        <meta property="og:type" content="website" />
        <meta name="robots" content="index,follow" />
        <link rel="canonical" href="/" />
      </Head>

      <MainLayout>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          {/* Welcome Banner */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <WelcomeBanner />
            </div>
          </div>

          {/* Main Content */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column - Main Actions */}
              <div className="lg:col-span-2 space-y-8">
                {/* Search Interface */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                  <div className="mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                      Search Your Documents
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400">
                      Ask questions about your documents or search for specific information
                    </p>
                  </div>
                  <SearchInterface 
                    onSearch={(query) => setSearchQuery(query)}
                    placeholder="Ask anything about your documents..."
                  />
                </div>

                {/* Statistics Cards */}
                <StatisticsCards />

                {/* Quick Actions */}
                <QuickActions />
              </div>

              {/* Right Column - Secondary Content */}
              <div className="space-y-8">
                {/* Recent Documents */}
                <RecentDocuments />
                
                {/* Activity Feed */}
                <ActivityFeed />
              </div>
            </div>
          </div>
        </div>
      </MainLayout>
    </>
  )
}

// Remove the getStaticProps that was using i18n
// export const getStaticProps: GetStaticProps = async ({ locale }) => {
//   return {
//     props: {
//       ...(await serverSideTranslations(locale ?? 'en', ['common', 'dashboard'])),
//       locale: locale ?? 'en',
//     },
//   }
// }