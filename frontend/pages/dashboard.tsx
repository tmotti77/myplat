import React from 'react';
import Head from 'next/head';
import { MainLayout } from '@/components/layouts/main-layout';
import { StatisticsCards } from '@/components/dashboard/statistics-cards';
import { WelcomeBanner } from '@/components/dashboard/welcome-banner';
import { RecentDocuments } from '@/components/documents/recent-documents';
import { ActivityFeed } from '@/components/dashboard/activity-feed';
import QuickActions from '@/components/dashboard/quick-actions';

export default function DashboardPage() {
  return (
    <>
      <Head>
        <title>Dashboard | Hybrid RAG Platform</title>
        <meta name="description" content="Your AI-powered document analysis dashboard" />
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
  );
}