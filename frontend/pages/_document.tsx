import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html>
      <Head>
        {/* Critical CSS for font loading */}
        <style
          dangerouslySetInnerHTML={{
            __html: `
              /* Font face declarations for better loading */
              @font-face {
                font-family: 'Inter';
                font-style: normal;
                font-weight: 100 900;
                font-display: swap;
                src: url('/fonts/inter-var.woff2') format('woff2');
                unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
              }
              
              @font-face {
                font-family: 'Heebo';
                font-style: normal;
                font-weight: 100 900;
                font-display: swap;
                src: url('/fonts/heebo-var.woff2') format('woff2');
                unicode-range: U+0590-05FF, U+200C-2010, U+20AA, U+25CC, U+FB1D-FB4F;
              }
              
              @font-face {
                font-family: 'Noto Sans Arabic';
                font-style: normal;
                font-weight: 100 900;
                font-display: swap;
                src: url('/fonts/noto-arabic-var.woff2') format('woff2');
                unicode-range: U+0600-06FF, U+200C-200E, U+2010-2011, U+204F, U+2E41, U+FB50-FDFF, U+FE80-FEFC;
              }
              
              /* Critical loading styles */
              .loading-skeleton {
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                background-size: 200px 100%;
                background-repeat: no-repeat;
                animation: loading 1.5s ease-in-out infinite;
              }
              
              @keyframes loading {
                0% { background-position: -200px 0; }
                100% { background-position: calc(200px + 100%) 0; }
              }
              
              /* Prevent flash of unstyled content */
              html {
                visibility: hidden;
              }
              
              html.fonts-loaded {
                visibility: visible;
              }
              
              /* Dark mode preference detection */
              @media (prefers-color-scheme: dark) {
                :root {
                  color-scheme: dark;
                }
              }
              
              /* Reduced motion preferences */
              @media (prefers-reduced-motion: reduce) {
                *,
                *::before,
                *::after {
                  animation-duration: 0.01ms !important;
                  animation-iteration-count: 1 !important;
                  transition-duration: 0.01ms !important;
                  scroll-behavior: auto !important;
                }
              }
              
              /* High contrast mode */
              @media (prefers-contrast: high) {
                * {
                  text-shadow: none !important;
                  box-shadow: none !important;
                }
              }
              
              /* Focus management */
              .js-focus-visible :focus:not(.focus-visible) {
                outline: none;
              }
              
              /* Print styles */
              @media print {
                .no-print, .no-print * {
                  display: none !important;
                }
                
                * {
                  color-adjust: exact !important;
                }
              }
            `,
          }}
        />

        {/* Preload critical resources */}
        <link
          rel="preload"
          href="/fonts/inter-var.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <link
          rel="preload"
          href="/fonts/heebo-var.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <link
          rel="preload"
          href="/fonts/noto-arabic-var.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />

        {/* Critical script for theme detection */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                function setTheme(theme) {
                  document.documentElement.classList.remove('light', 'dark');
                  document.documentElement.classList.add(theme);
                  document.documentElement.style.colorScheme = theme;
                }
                
                function getTheme() {
                  try {
                    const stored = localStorage.getItem('theme');
                    if (stored && ['light', 'dark', 'system'].includes(stored)) {
                      if (stored === 'system') {
                        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                      }
                      return stored;
                    }
                  } catch (e) {}
                  
                  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                }
                
                setTheme(getTheme());
                
                // Listen for system theme changes
                window.matchMedia('(prefers-color-scheme: dark)').addListener(function(e) {
                  try {
                    const stored = localStorage.getItem('theme');
                    if (stored === 'system' || !stored) {
                      setTheme(e.matches ? 'dark' : 'light');
                    }
                  } catch (e) {}
                });
              })();
            `,
          }}
        />

        {/* Font loading optimization */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                if ('fonts' in document) {
                  Promise.all([
                    document.fonts.load('400 1em Inter'),
                    document.fonts.load('600 1em Inter'),
                    document.fonts.load('400 1em Heebo'),
                    document.fonts.load('400 1em "Noto Sans Arabic"')
                  ]).then(function() {
                    document.documentElement.classList.add('fonts-loaded');
                  }).catch(function() {
                    document.documentElement.classList.add('fonts-loaded');
                  });
                  
                  // Fallback timeout
                  setTimeout(function() {
                    document.documentElement.classList.add('fonts-loaded');
                  }, 3000);
                } else {
                  document.documentElement.classList.add('fonts-loaded');
                }
              })();
            `,
          }}
        />

        {/* Direction and language detection */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
                const lang = document.documentElement.lang || 'en';
                const dir = rtlLanguages.includes(lang) ? 'rtl' : 'ltr';
                document.documentElement.dir = dir;
                document.documentElement.dataset.direction = dir;
              })();
            `,
          }}
        />

        {/* Accessibility enhancements */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // Add focus-visible polyfill behavior
                function applyFocusVisiblePolyfill() {
                  var hadKeyboardEvent = true;
                  var keyboardThrottleTimeoutID = 0;
                  
                  function onKeyDown(e) {
                    if (e.metaKey || e.altKey || e.ctrlKey) {
                      return;
                    }
                    hadKeyboardEvent = true;
                  }
                  
                  function onPointerDown() {
                    hadKeyboardEvent = false;
                  }
                  
                  function onFocus(e) {
                    if (hadKeyboardEvent || e.target.matches(':focus-visible')) {
                      e.target.classList.add('focus-visible');
                    }
                  }
                  
                  function onBlur(e) {
                    e.target.classList.remove('focus-visible');
                  }
                  
                  document.addEventListener('keydown', onKeyDown, true);
                  document.addEventListener('mousedown', onPointerDown, true);
                  document.addEventListener('pointerdown', onPointerDown, true);
                  document.addEventListener('touchstart', onPointerDown, true);
                  document.addEventListener('focus', onFocus, true);
                  document.addEventListener('blur', onBlur, true);
                  
                  document.body.classList.add('js-focus-visible');
                }
                
                if (!CSS.supports('selector(:focus-visible)')) {
                  applyFocusVisiblePolyfill();
                }
                
                // High contrast detection
                if (window.matchMedia('(prefers-contrast: high)').matches) {
                  document.documentElement.classList.add('high-contrast');
                }
                
                window.matchMedia('(prefers-contrast: high)').addListener(function(e) {
                  document.documentElement.classList.toggle('high-contrast', e.matches);
                });
                
                // Reduced motion detection
                if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                  document.documentElement.classList.add('reduce-motion');
                }
                
                window.matchMedia('(prefers-reduced-motion: reduce)').addListener(function(e) {
                  document.documentElement.classList.toggle('reduce-motion', e.matches);
                });
              })();
            `,
          }}
        />

        {/* Performance monitoring */}
        {process.env.NODE_ENV === 'production' && (
          <script
            dangerouslySetInnerHTML={{
              __html: `
                (function() {
                  // Core Web Vitals monitoring
                  function sendToAnalytics(metric) {
                    if (typeof gtag !== 'undefined') {
                      gtag('event', metric.name, {
                        event_category: 'Web Vitals',
                        event_label: metric.id,
                        value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
                        non_interaction: true,
                      });
                    }
                  }
                  
                  // Load web-vitals library
                  import('https://unpkg.com/web-vitals@3/dist/web-vitals.iife.js').then(function(webVitals) {
                    webVitals.getCLS(sendToAnalytics);
                    webVitals.getFID(sendToAnalytics);
                    webVitals.getFCP(sendToAnalytics);
                    webVitals.getLCP(sendToAnalytics);
                    webVitals.getTTFB(sendToAnalytics);
                  }).catch(function() {
                    // Silently fail if web-vitals can't be loaded
                  });
                })();
              `,
            }}
          />
        )}
      </Head>
      <body>
        {/* Loading fallback */}
        <noscript>
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: '#ffffff',
            color: '#000000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'system-ui, sans-serif',
            textAlign: 'center',
            padding: '2rem'
          }}>
            <div>
              <h1>JavaScript Required</h1>
              <p>This application requires JavaScript to function properly. Please enable JavaScript in your browser.</p>
            </div>
          </div>
        </noscript>

        <Main />
        <NextScript />
      </body>
    </Html>
  )
}