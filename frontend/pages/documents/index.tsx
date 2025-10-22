import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { MainLayout } from '@/components/layouts/main-layout';
import { 
  FileText, 
  Upload, 
  Search, 
  Filter, 
  MoreVertical,
  Download,
  Trash2,
  Eye,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader,
  Grid,
  List,
  RefreshCw
} from 'lucide-react';

interface Document {
  id: string;
  title: string;
  filename: string;
  file_size: number;
  file_type: string;
  status: 'UPLOADING' | 'PROCESSING' | 'PROCESSED' | 'FAILED' | 'ARCHIVED';
  upload_date: string;
  last_updated: string;
  processed_chunks: number;
  total_chunks: number;
  language: string;
  category?: string;
  tags: string[];
  description?: string;
  user_id: string;
}

interface DocumentsResponse {
  documents: Document[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function DocumentsPage() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());

  const pageSize = 20;

  useEffect(() => {
    loadDocuments();
    loadCategories();
  }, [currentPage, statusFilter, categoryFilter, searchTerm]);

  const loadDocuments = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        sort_by: 'upload_date',
        sort_order: 'desc',
      });

      if (statusFilter !== 'all') {
        params.append('status_filter', statusFilter);
      }
      if (categoryFilter !== 'all') {
        params.append('category', categoryFilter);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data: DocumentsResponse = await response.json();
        setDocuments(data.documents);
        setTotalPages(data.total_pages);
        setTotalCount(data.total_count);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/search/categories`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCategories(data.categories || []);
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'UPLOADING':
        return <Loader className="animate-spin h-4 w-4 text-blue-500" />;
      case 'PROCESSING':
        return <Loader className="animate-spin h-4 w-4 text-yellow-500" />;
      case 'PROCESSED':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'FAILED':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'ARCHIVED':
        return <Clock className="h-4 w-4 text-gray-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'UPLOADING': return t('uploading');
      case 'PROCESSING': return t('processing');
      case 'PROCESSED': return t('processed');
      case 'FAILED': return t('failed');
      case 'ARCHIVED': return t('archived');
      default: return status;
    }
  };

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'UPLOADING': return 'bg-blue-100 text-blue-800';
      case 'PROCESSING': return 'bg-yellow-100 text-yellow-800';
      case 'PROCESSED': return 'bg-green-100 text-green-800';
      case 'FAILED': return 'bg-red-100 text-red-800';
      case 'ARCHIVED': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString([], {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleDocumentSelect = (documentId: string) => {
    const newSelected = new Set(selectedDocuments);
    if (newSelected.has(documentId)) {
      newSelected.delete(documentId);
    } else {
      newSelected.add(documentId);
    }
    setSelectedDocuments(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedDocuments.size === documents.length) {
      setSelectedDocuments(new Set());
    } else {
      setSelectedDocuments(new Set(documents.map(doc => doc.id)));
    }
  };

  const deleteDocument = async (documentId: string) => {
    if (!confirm(t('confirm_delete_document'))) return;

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents/${documentId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
        setTotalCount(prev => prev - 1);
      }
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const downloadDocument = async (documentId: string, filename: string) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents/${documentId}/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error downloading document:', error);
    }
  };

  const DocumentCard = ({ document }: { document: Document }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-4">
        <FileText className="h-8 w-8 text-blue-500 flex-shrink-0 mt-1" />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-900 truncate">
                {document.title}
              </h3>
              <p className="text-sm text-gray-500 mt-1">{document.filename}</p>
            </div>
            
            <div className="flex items-center space-x-2 ml-4">
              {getStatusIcon(document.status)}
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                {getStatusText(document.status)}
              </span>
            </div>
          </div>
          
          {document.description && (
            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
              {document.description}
            </p>
          )}
          
          <div className="flex items-center space-x-4 mt-4 text-sm text-gray-500">
            <span>{formatFileSize(document.file_size)}</span>
            <span>{formatDate(document.upload_date)}</span>
            {document.category && (
              <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                {document.category}
              </span>
            )}
          </div>
          
          {document.status === 'PROCESSING' && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{t('processing_progress')}</span>
                <span>{document.processed_chunks}/{document.total_chunks}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: document.total_chunks > 0 
                      ? `${(document.processed_chunks / document.total_chunks) * 100}%` 
                      : '0%' 
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center space-x-2">
          {document.tags.slice(0, 3).map(tag => (
            <span key={tag} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
              {tag}
            </span>
          ))}
          {document.tags.length > 3 && (
            <span className="text-xs text-gray-500">+{document.tags.length - 3}</span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => router.push(`/documents/${document.id}`)}
            className="text-gray-600 hover:text-gray-900 p-1"
            title={t('view_document')}
          >
            <Eye size={16} />
          </button>
          <button
            onClick={() => downloadDocument(document.id, document.filename)}
            className="text-gray-600 hover:text-gray-900 p-1"
            title={t('download')}
          >
            <Download size={16} />
          </button>
          <button
            onClick={() => deleteDocument(document.id)}
            className="text-red-600 hover:text-red-700 p-1"
            title={t('delete')}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('documents')}</h1>
            <p className="text-gray-600">{t('manage_your_documents')}</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <Link
              href="/documents/upload"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2 transition-colors"
            >
              <Upload size={16} />
              <span>{t('upload_document')}</span>
            </Link>
            
            <button
              onClick={loadDocuments}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title={t('refresh')}
            >
              <RefreshCw size={16} />
            </button>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 flex-1">
              {/* Search */}
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder={t('search_documents')}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">{t('all_statuses')}</option>
                <option value="PROCESSED">{t('processed')}</option>
                <option value="PROCESSING">{t('processing')}</option>
                <option value="FAILED">{t('failed')}</option>
              </select>

              {/* Category Filter */}
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">{t('all_categories')}</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'list' 
                    ? 'bg-blue-100 text-blue-600' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <List size={16} />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition-colors ${
                  viewMode === 'grid' 
                    ? 'bg-blue-100 text-blue-600' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Grid size={16} />
              </button>
            </div>
          </div>

          {/* Results Summary */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              {t('showing_results', { 
                start: ((currentPage - 1) * pageSize) + 1,
                end: Math.min(currentPage * pageSize, totalCount),
                total: totalCount 
              })}
            </p>
            
            {selectedDocuments.size > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  {selectedDocuments.size} {t('selected')}
                </span>
                <button className="text-red-600 hover:text-red-700 text-sm font-medium">
                  {t('delete_selected')}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Documents */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader className="animate-spin h-8 w-8 text-blue-600" />
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12">
            <FileText size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {t('no_documents_found')}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchTerm || statusFilter !== 'all' || categoryFilter !== 'all'
                ? t('try_adjusting_filters')
                : t('upload_first_document')
              }
            </p>
            {!searchTerm && statusFilter === 'all' && categoryFilter === 'all' && (
              <Link
                href="/documents/upload"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium inline-flex items-center space-x-2 transition-colors"
              >
                <Upload size={16} />
                <span>{t('upload_document')}</span>
              </Link>
            )}
          </div>
        ) : (
          <>
            <div className={
              viewMode === 'grid' 
                ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6'
                : 'space-y-4'
            }>
              {documents.map(document => (
                viewMode === 'grid' ? (
                  <DocumentCard key={document.id} document={document} />
                ) : (
                  <div key={document.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center space-x-4">
                      <input
                        type="checkbox"
                        checked={selectedDocuments.has(document.id)}
                        onChange={() => handleDocumentSelect(document.id)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      
                      <FileText className="h-8 w-8 text-blue-500 flex-shrink-0" />
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h3 className="text-sm font-medium text-gray-900 truncate">
                              {document.title}
                            </h3>
                            <p className="text-xs text-gray-500">{document.filename}</p>
                          </div>
                          
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>{formatFileSize(document.file_size)}</span>
                            <span>{formatDate(document.upload_date)}</span>
                            <div className="flex items-center space-x-1">
                              {getStatusIcon(document.status)}
                              <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(document.status)}`}>
                                {getStatusText(document.status)}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        {document.status === 'PROCESSING' && (
                          <div className="mt-2">
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div 
                                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                style={{ 
                                  width: document.total_chunks > 0 
                                    ? `${(document.processed_chunks / document.total_chunks) * 100}%` 
                                    : '0%' 
                                }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => router.push(`/documents/${document.id}`)}
                          className="text-gray-600 hover:text-gray-900 p-1"
                          title={t('view_document')}
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          onClick={() => downloadDocument(document.id, document.filename)}
                          className="text-gray-600 hover:text-gray-900 p-1"
                          title={t('download')}
                        >
                          <Download size={16} />
                        </button>
                        <button
                          onClick={() => deleteDocument(document.id)}
                          className="text-red-600 hover:text-red-700 p-1"
                          title={t('delete')}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                )
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center space-x-2 mt-8">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  {t('previous')}
                </button>
                
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + Math.max(1, currentPage - 2);
                  if (page > totalPages) return null;
                  
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-2 text-sm font-medium rounded-md ${
                        page === currentPage
                          ? 'text-blue-600 bg-blue-50 border border-blue-300'
                          : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  {t('next')}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </MainLayout>
  );
}

export async function getStaticProps({ locale }: { locale: string }) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ['common'])),
    },
  };
}