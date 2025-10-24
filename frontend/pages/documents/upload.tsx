import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { MainLayout } from '@/components/layouts/main-layout';
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Loader,
  File,
  Image,
  FileIcon
} from '@/lib/icon-mappings';

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  documentId?: string;
}

const ALLOWED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'text/markdown',
  'text/html',
  'application/json',
  'text/csv',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'
];

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

export default function DocumentUploadPage() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return FileText;
    if (fileType.includes('image')) return Image;
    if (fileType.includes('word') || fileType.includes('document')) return FileText;
    if (fileType.includes('excel') || fileType.includes('sheet')) return File;
    if (fileType.includes('powerpoint') || fileType.includes('presentation')) return File;
    return FileIcon;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return t('unsupported_file_type');
    }
    if (file.size > MAX_FILE_SIZE) {
      return t('file_too_large');
    }
    return null;
  };

  const handleFiles = useCallback((newFiles: FileList) => {
    const validFiles: UploadedFile[] = [];
    
    Array.from(newFiles).forEach(file => {
      const error = validateFile(file);
      const uploadedFile: UploadedFile = {
        file,
        id: Math.random().toString(36).substr(2, 9),
        status: error ? 'error' : 'pending',
        progress: 0,
      };
      
      if (error) {
        uploadedFile.error = error;
      }
      
      validFiles.push(uploadedFile);
    });

    setFiles(prev => [...prev, ...validFiles]);
  }, [t]);

  const uploadFile = async (uploadFile: UploadedFile): Promise<void> => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Update status to uploading
    setFiles(prev => prev.map(f => 
      f.id === uploadFile.id 
        ? { ...f, status: 'uploading', progress: 0 }
        : f
    ));

    const formData = new FormData();
    formData.append('file', uploadFile.file);
    formData.append('title', uploadFile.file.name.split('.')[0] || uploadFile.file.name);
    formData.append('language', 'en');
    formData.append('processing_options', JSON.stringify({}));

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents/upload`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      
      // Update status to success
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: 'success', 
              progress: 100, 
              documentId: result.document_id 
            }
          : f
      ));

    } catch (error) {
      // Update status to error
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { 
              ...f, 
              status: 'error', 
              progress: 0,
              error: error instanceof Error ? error.message : 'Upload failed'
            }
          : f
      ));
    }
  };

  const uploadAllFiles = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    
    // Upload files concurrently (max 3 at a time)
    const batchSize = 3;
    for (let i = 0; i < pendingFiles.length; i += batchSize) {
      const batch = pendingFiles.slice(i, i + batchSize);
      await Promise.all(batch.map(uploadFile));
    }
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const retryFile = (fileId: string) => {
    const file = files.find(f => f.id === fileId);
    if (file) {
      uploadFile(file);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const pendingFiles = files.filter(f => f.status === 'pending');
  const successFiles = files.filter(f => f.status === 'success');
  const errorFiles = files.filter(f => f.status === 'error');
  const uploadingFiles = files.filter(f => f.status === 'uploading');

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">{t('upload_documents')}</h1>
          <p className="text-gray-600 mt-2">{t('upload_documents_description')}</p>
        </div>

        {/* Upload Area */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging 
              ? 'border-blue-400 bg-blue-50' 
              : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.md,.html,.json,.csv,.xlsx,.xls,.pptx,.ppt"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          <div className="space-y-4">
            <Upload 
              className={`mx-auto h-16 w-16 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} 
            />
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragging ? t('drop_files_here') : t('drag_drop_files')}
              </p>
              <p className="text-gray-600 mt-1">{t('or_click_to_browse')}</p>
            </div>
            
            {/* Supported formats */}
            <div className="text-sm text-gray-500">
              <p>{t('supported_formats')}: PDF, Word, Excel, PowerPoint, Text, HTML, JSON, CSV</p>
              <p>{t('max_file_size')}: 100MB</p>
            </div>
          </div>
        </div>

        {/* Upload Controls */}
        {pendingFiles.length > 0 && (
          <div className="flex justify-between items-center bg-white rounded-lg shadow p-4">
            <p className="text-gray-600">
              {pendingFiles.length} {t('files_ready_to_upload')}
            </p>
            <button
              onClick={uploadAllFiles}
              disabled={uploadingFiles.length > 0}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
            >
              {uploadingFiles.length > 0 ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  <span>{t('uploading')}</span>
                </>
              ) : (
                <>
                  <Upload size={16} />
                  <span>{t('upload_all')}</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* File List */}
        {files.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">{t('upload_queue')}</h3>
            </div>
            
            <div className="divide-y divide-gray-200">
              {files.map(uploadedFile => {
                const FileIcon = getFileIcon(uploadedFile.file.type);
                
                return (
                  <div key={uploadedFile.id} className="px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-4 flex-1">
                      <FileIcon className="h-8 w-8 text-gray-400 flex-shrink-0" />
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {uploadedFile.file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(uploadedFile.file.size)}
                        </p>
                        
                        {/* Progress bar for uploading */}
                        {uploadedFile.status === 'uploading' && (
                          <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                              style={{ width: `${uploadedFile.progress}%` }}
                            />
                          </div>
                        )}
                        
                        {/* Error message */}
                        {uploadedFile.status === 'error' && uploadedFile.error && (
                          <p className="text-xs text-red-600 mt-1">{uploadedFile.error}</p>
                        )}
                      </div>
                    </div>
                    
                    {/* Status and actions */}
                    <div className="flex items-center space-x-3">
                      {uploadedFile.status === 'pending' && (
                        <span className="text-xs text-gray-500">{t('pending')}</span>
                      )}
                      
                      {uploadedFile.status === 'uploading' && (
                        <div className="flex items-center space-x-2">
                          <Loader className="animate-spin h-4 w-4 text-blue-600" />
                          <span className="text-xs text-blue-600">{t('uploading')}</span>
                        </div>
                      )}
                      
                      {uploadedFile.status === 'success' && (
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          <span className="text-xs text-green-600">{t('uploaded')}</span>
                        </div>
                      )}
                      
                      {uploadedFile.status === 'error' && (
                        <div className="flex items-center space-x-2">
                          <AlertCircle className="h-4 w-4 text-red-600" />
                          <button
                            onClick={() => retryFile(uploadedFile.id)}
                            className="text-xs text-blue-600 hover:text-blue-700 underline"
                          >
                            {t('retry')}
                          </button>
                        </div>
                      )}
                      
                      <button
                        onClick={() => removeFile(uploadedFile.id)}
                        className="text-gray-400 hover:text-gray-600"
                        disabled={uploadedFile.status === 'uploading'}
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Success Summary */}
        {successFiles.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <h3 className="text-sm font-medium text-green-800">
                {t('upload_complete')}
              </h3>
            </div>
            <p className="text-sm text-green-700 mt-1">
              {successFiles.length} {t('files_uploaded_successfully')}. {t('processing_will_begin_shortly')}.
            </p>
            <button
              onClick={() => router.push('/documents')}
              className="mt-3 text-sm bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-medium"
            >
              {t('view_documents')}
            </button>
          </div>
        )}

        {/* Error Summary */}
        {errorFiles.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <h3 className="text-sm font-medium text-red-800">
                {t('upload_errors')}
              </h3>
            </div>
            <p className="text-sm text-red-700 mt-1">
              {errorFiles.length} {t('files_failed_to_upload')}. {t('please_check_and_retry')}.
            </p>
          </div>
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