import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { MainLayout } from '@/components/layouts/main-layout';
import { 
  Send, 
  Bot, 
  User, 
  Loader, 
  MessageSquare,
  FileText,
  ExternalLink,
  RefreshCw,
  Settings,
  Plus
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Source[];
  processing_time_ms?: number;
}

interface Source {
  chunk_id: string;
  document_id: string;
  document_title: string;
  content: string;
  score: number;
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

interface ChatSettings {
  model: string;
  temperature: number;
  max_tokens: number;
  include_sources: boolean;
}

export default function ChatPage() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSources, setShowSources] = useState(true);
  const [settings, setSettings] = useState<ChatSettings>({
    model: 'gpt-4-turbo-preview',
    temperature: 0.1,
    max_tokens: 2000,
    include_sources: true,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation messages when conversation changes
  useEffect(() => {
    if (currentConversationId) {
      loadConversationMessages(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat/conversations`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadConversationMessages = async (conversationId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat/conversations/${conversationId}/messages`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat/chat`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: inputMessage,
            conversation_id: currentConversationId,
            model: settings.model,
            temperature: settings.temperature,
            max_tokens: settings.max_tokens,
            include_sources: settings.include_sources,
            stream: false,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();

      // Update current conversation ID if it's a new conversation
      if (!currentConversationId) {
        setCurrentConversationId(data.conversation_id);
        loadConversations(); // Refresh conversations list
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.content,
        timestamp: new Date().toISOString(),
        sources: data.sources,
        processing_time_ms: data.processing_time_ms,
      };

      setMessages(prev => [...prev.slice(0, -1), userMessage, assistantMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      // Remove the temporary user message on error
      setMessages(prev => prev.slice(0, -1));
      // You could add an error message here
    } finally {
      setIsLoading(false);
    }
  };

  const startNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
    inputRef.current?.focus();
  };

  const selectConversation = (conversationId: string) => {
    setCurrentConversationId(conversationId);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const truncateText = (text: string, maxLength: number) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <MainLayout>
      <div className="flex h-[calc(100vh-4rem)] bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 border-r border-gray-200 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <button
              onClick={startNewConversation}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium flex items-center justify-center space-x-2 transition-colors"
            >
              <Plus size={16} />
              <span>{t('new_chat')}</span>
            </button>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto p-2">
            <div className="space-y-1">
              {conversations.map(conversation => (
                <button
                  key={conversation.id}
                  onClick={() => selectConversation(conversation.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    currentConversationId === conversation.id
                      ? 'bg-blue-50 border-blue-200 border'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <MessageSquare 
                      size={16} 
                      className={`mt-1 flex-shrink-0 ${
                        currentConversationId === conversation.id 
                          ? 'text-blue-600' 
                          : 'text-gray-400'
                      }`} 
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {truncateText(conversation.title, 50)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {conversation.message_count} {t('messages')} • {formatTime(conversation.updated_at)}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
              
              {conversations.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare size={32} className="mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">{t('no_conversations_yet')}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                {currentConversationId ? t('conversation') : t('new_conversation')}
              </h1>
              <p className="text-sm text-gray-500">{t('ai_powered_chat')}</p>
            </div>
            <div className="flex items-center space-x-2">
              <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                <Settings size={16} />
              </button>
              <button 
                onClick={() => setShowSources(!showSources)}
                className={`p-2 rounded-lg transition-colors ${
                  showSources 
                    ? 'text-blue-600 bg-blue-50' 
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FileText size={16} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot size={64} className="text-gray-300 mb-4" />
                <h2 className="text-xl font-medium text-gray-700 mb-2">
                  {t('start_conversation')}
                </h2>
                <p className="text-gray-500 max-w-md">
                  {t('ask_questions_about_documents')}
                </p>
              </div>
            ) : (
              messages.map(message => (
                <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-3xl flex space-x-3 ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    {/* Avatar */}
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user' ? 'bg-blue-600' : 'bg-gray-200'
                    }`}>
                      {message.role === 'user' ? (
                        <User size={16} className="text-white" />
                      ) : (
                        <Bot size={16} className="text-gray-600" />
                      )}
                    </div>

                    {/* Message Content */}
                    <div className="flex-1">
                      <div className={`p-4 rounded-2xl ${
                        message.role === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 text-gray-900'
                      }`}>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      </div>

                      {/* Message Meta */}
                      <div className={`flex items-center space-x-2 mt-1 text-xs text-gray-500 ${
                        message.role === 'user' ? 'justify-end' : ''
                      }`}>
                        <span>{formatTime(message.timestamp)}</span>
                        {message.processing_time_ms && (
                          <span>• {message.processing_time_ms}ms</span>
                        )}
                      </div>

                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && showSources && (
                        <div className="mt-3 border border-gray-200 rounded-lg p-3 bg-gray-50">
                          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                            <FileText size={14} className="mr-1" />
                            {t('sources')} ({message.sources.length})
                          </h4>
                          <div className="space-y-2">
                            {message.sources.slice(0, 3).map((source, index) => (
                              <div key={index} className="bg-white rounded p-2 border border-gray-100">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-xs font-medium text-blue-600 truncate">
                                    {source.document_title}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {Math.round(source.score * 100)}%
                                  </span>
                                </div>
                                <p className="text-xs text-gray-600">
                                  {truncateText(source.content, 150)}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}

            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-3xl flex space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <Bot size={16} className="text-gray-600" />
                  </div>
                  <div className="flex-1">
                    <div className="bg-gray-100 p-4 rounded-2xl">
                      <div className="flex items-center space-x-2">
                        <Loader className="animate-spin" size={16} />
                        <span className="text-gray-600">{t('thinking')}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-4">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={t('type_your_message')}
                  disabled={isLoading}
                  className="w-full p-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none max-h-32 disabled:bg-gray-50 disabled:cursor-not-allowed"
                  rows={1}
                  style={{ 
                    height: 'auto',
                    minHeight: '48px',
                    maxHeight: '128px' 
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = 'auto';
                    target.style.height = target.scrollHeight + 'px';
                  }}
                />
              </div>
              
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white p-3 rounded-lg transition-colors flex-shrink-0"
              >
                {isLoading ? (
                  <Loader className="animate-spin" size={20} />
                ) : (
                  <Send size={20} />
                )}
              </button>
            </div>
            
            <p className="text-xs text-gray-500 mt-2">
              {t('press_enter_to_send')}
            </p>
          </div>
        </div>
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