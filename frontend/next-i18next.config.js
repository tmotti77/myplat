/** @type {import('next-i18next').UserConfig} */
module.exports = {
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'he', 'ar', 'es', 'fr', 'de'],
    localeDetection: false,
    domains: [
      {
        domain: 'myplatform.com',
        defaultLocale: 'en',
      },
      {
        domain: 'myplatform.co.il',
        defaultLocale: 'he',
      },
      {
        domain: 'myplatform.ae',
        defaultLocale: 'ar',
      },
    ],
  },
  
  // Namespace configuration
  ns: [
    'common',
    'navigation',
    'auth',
    'dashboard',
    'search',
    'documents',
    'settings',
    'admin',
    'errors',
    'validation',
  ],
  
  // Default namespace
  defaultNS: 'common',
  
  // Fallback language
  fallbackLng: 'en',
  
  // Debug mode in development
  debug: process.env.NODE_ENV === 'development',
  
  // React options
  react: {
    useSuspense: false,
    bindI18n: 'languageChanged loaded',
    bindI18nStore: 'added removed',
    transEmptyNodeValue: '',
    transSupportBasicHtmlNodes: true,
    transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em', 'u', 'code'],
  },
  
  // Backend options for server-side
  backend: {
    loadPath: '/locales/{{lng}}/{{ns}}.json',
  },
  
  // Interpolation options
  interpolation: {
    escapeValue: false, // React already escapes
    formatSeparator: ',',
    format: function(value, format, lng) {
      if (format === 'uppercase') return value.toUpperCase()
      if (format === 'lowercase') return value.toLowerCase()
      if (format === 'currency') {
        return new Intl.NumberFormat(lng, {
          style: 'currency',
          currency: lng === 'he' ? 'ILS' : lng === 'ar' ? 'AED' : 'USD'
        }).format(value)
      }
      if (format === 'date') {
        return new Intl.DateTimeFormat(lng).format(new Date(value))
      }
      if (format === 'relativeTime') {
        const rtf = new Intl.RelativeTimeFormat(lng, { numeric: 'auto' })
        const diff = Math.floor((new Date(value) - new Date()) / (1000 * 60 * 60 * 24))
        return rtf.format(diff, 'day')
      }
      return value
    }
  },
  
  // Load only current language and fallback
  load: 'languageOnly',
  
  // Cache translations
  cache: {
    enabled: true,
    prefix: 'i18next_res_',
    expirationTime: 7 * 24 * 60 * 60 * 1000, // 7 days
  },
  
  // Detection options
  detection: {
    order: ['path', 'cookie', 'htmlTag', 'localStorage', 'subdomain', 'header'],
    caches: ['localStorage', 'cookie'],
    excludeCacheFor: ['cimode'],
    cookieMinutes: 60 * 24 * 30, // 30 days
    cookieDomain: process.env.NODE_ENV === 'production' ? '.myplatform.com' : 'localhost',
    lookupLocalStorage: 'i18nextLng',
    lookupCookie: 'next-i18next',
    lookupFromPathIndex: 0,
    lookupFromSubdomainIndex: 0,
    htmlTag: typeof document !== 'undefined' ? document.documentElement : null,
  },
  
  // Server-side options
  serializeConfig: false,
  strictMode: true,
  
  // Custom resource loading for better performance
  partialBundledLanguages: true,
  
  // RTL support configuration
  rtl: {
    languages: ['ar', 'he'],
    defaultDirection: 'ltr',
  },
  
  // Pluralization rules for Hebrew and Arabic
  pluralSeparator: '_',
  contextSeparator: '_',
  
  // Custom post processors for RTL
  postProcess: ['rtl'],
  
  // Locale data for Intl APIs
  localeData: {
    en: {
      dir: 'ltr',
      name: 'English',
      nativeName: 'English',
      currency: 'USD',
      dateFormat: 'MM/DD/YYYY',
      timeFormat: '12h',
    },
    he: {
      dir: 'rtl',
      name: 'Hebrew',
      nativeName: 'עברית',
      currency: 'ILS',
      dateFormat: 'DD/MM/YYYY',
      timeFormat: '24h',
    },
    ar: {
      dir: 'rtl',
      name: 'Arabic',
      nativeName: 'العربية',
      currency: 'AED',
      dateFormat: 'DD/MM/YYYY',
      timeFormat: '24h',
    },
    es: {
      dir: 'ltr',
      name: 'Spanish',
      nativeName: 'Español',
      currency: 'EUR',
      dateFormat: 'DD/MM/YYYY',
      timeFormat: '24h',
    },
    fr: {
      dir: 'ltr',
      name: 'French',
      nativeName: 'Français',
      currency: 'EUR',
      dateFormat: 'DD/MM/YYYY',
      timeFormat: '24h',
    },
    de: {
      dir: 'ltr',
      name: 'German',
      nativeName: 'Deutsch',
      currency: 'EUR',
      dateFormat: 'DD.MM.YYYY',
      timeFormat: '24h',
    },
  },
}