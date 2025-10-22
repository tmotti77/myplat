/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      // RTL-aware spacing and positioning
      spacing: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
      
      // Enhanced color palette with accessibility in mind
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50: 'hsl(var(--primary-50))',
          100: 'hsl(var(--primary-100))',
          200: 'hsl(var(--primary-200))',
          300: 'hsl(var(--primary-300))',
          400: 'hsl(var(--primary-400))',
          500: 'hsl(var(--primary-500))',
          600: 'hsl(var(--primary-600))',
          700: 'hsl(var(--primary-700))',
          800: 'hsl(var(--primary-800))',
          900: 'hsl(var(--primary-900))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
        },
        info: {
          DEFAULT: 'hsl(var(--info))',
          foreground: 'hsl(var(--info-foreground))',
        },
      },
      
      // RTL-aware border radius
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      
      // Typography optimized for multiple languages
      fontFamily: {
        sans: [
          'Inter', 
          'system-ui', 
          '-apple-system', 
          'BlinkMacSystemFont', 
          'Segoe UI', 
          'Roboto', 
          'Helvetica Neue', 
          'Arial', 
          'Noto Sans', 
          'sans-serif',
          'Apple Color Emoji',
          'Segoe UI Emoji',
          'Segoe UI Symbol',
          'Noto Color Emoji'
        ],
        hebrew: [
          'Heebo',
          'Assistant',
          'system-ui',
          '-apple-system',
          'sans-serif'
        ],
        arabic: [
          'Noto Sans Arabic',
          'Tahoma',
          'system-ui',
          '-apple-system',
          'sans-serif'
        ],
        mono: [
          'Fira Code',
          'JetBrains Mono',
          'Menlo',
          'Monaco',
          'Consolas',
          'Liberation Mono',
          'Courier New',
          'monospace'
        ],
      },
      
      // Enhanced font sizes with line heights
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
        '7xl': ['4.5rem', { lineHeight: '1' }],
        '8xl': ['6rem', { lineHeight: '1' }],
        '9xl': ['8rem', { lineHeight: '1' }],
      },
      
      // Enhanced animations with reduced motion support
      keyframes: {
        'accordion-down': {
          from: { height: 0 },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: 0 },
        },
        'fade-in': {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        'fade-out': {
          '0%': { opacity: 1 },
          '100%': { opacity: 0 },
        },
        'slide-in-left': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-in-up': {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        'slide-in-down': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.8 },
        },
        'bounce-subtle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-2px)' },
        },
        'shimmer': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'fade-out': 'fade-out 0.3s ease-out',
        'slide-in-left': 'slide-in-left 0.3s ease-out',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'slide-in-up': 'slide-in-up 0.3s ease-out',
        'slide-in-down': 'slide-in-down 0.3s ease-out',
        'pulse-subtle': 'pulse-subtle 2s ease-in-out infinite',
        'bounce-subtle': 'bounce-subtle 1s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
      },
      
      // Enhanced shadows with focus states
      boxShadow: {
        'focus-ring': '0 0 0 2px hsl(var(--ring))',
        'focus-ring-offset': '0 0 0 2px hsl(var(--background)), 0 0 0 4px hsl(var(--ring))',
        'elevated': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'elevated-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
      
      // Z-index scale
      zIndex: {
        'dropdown': '1000',
        'sticky': '1020',
        'fixed': '1030',
        'modal-backdrop': '1040',
        'modal': '1050',
        'popover': '1060',
        'tooltip': '1070',
        'toast': '1080',
      },
      
      // Screen sizes for responsive design
      screens: {
        'xs': '475px',
        '3xl': '1920px',
        '4xl': '2560px',
      },
      
      // Grid template columns for complex layouts
      gridTemplateColumns: {
        'sidebar': '250px 1fr',
        'sidebar-collapsed': '80px 1fr',
        'main-content': '1fr 300px',
        'chat': '1fr 350px',
      },
      
      // Backdrop blur utilities
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
    
    // Custom plugin for RTL support
    function({ addUtilities, addVariant, theme }) {
      // RTL variants
      addVariant('rtl', '[dir="rtl"] &')
      addVariant('ltr', '[dir="ltr"] &')
      
      // RTL-aware utilities
      addUtilities({
        '.text-start': {
          'text-align': 'start',
        },
        '.text-end': {
          'text-align': 'end',
        },
        '.float-start': {
          'float': 'inline-start',
        },
        '.float-end': {
          'float': 'inline-end',
        },
        '.border-start': {
          'border-inline-start-width': '1px',
        },
        '.border-end': {
          'border-inline-end-width': '1px',
        },
        '.rounded-start': {
          'border-start-start-radius': theme('borderRadius.DEFAULT'),
          'border-end-start-radius': theme('borderRadius.DEFAULT'),
        },
        '.rounded-end': {
          'border-start-end-radius': theme('borderRadius.DEFAULT'),
          'border-end-end-radius': theme('borderRadius.DEFAULT'),
        },
        '.ps-1': { 'padding-inline-start': theme('spacing.1') },
        '.ps-2': { 'padding-inline-start': theme('spacing.2') },
        '.ps-3': { 'padding-inline-start': theme('spacing.3') },
        '.ps-4': { 'padding-inline-start': theme('spacing.4') },
        '.ps-5': { 'padding-inline-start': theme('spacing.5') },
        '.ps-6': { 'padding-inline-start': theme('spacing.6') },
        '.pe-1': { 'padding-inline-end': theme('spacing.1') },
        '.pe-2': { 'padding-inline-end': theme('spacing.2') },
        '.pe-3': { 'padding-inline-end': theme('spacing.3') },
        '.pe-4': { 'padding-inline-end': theme('spacing.4') },
        '.pe-5': { 'padding-inline-end': theme('spacing.5') },
        '.pe-6': { 'padding-inline-end': theme('spacing.6') },
        '.ms-1': { 'margin-inline-start': theme('spacing.1') },
        '.ms-2': { 'margin-inline-start': theme('spacing.2') },
        '.ms-3': { 'margin-inline-start': theme('spacing.3') },
        '.ms-4': { 'margin-inline-start': theme('spacing.4') },
        '.ms-5': { 'margin-inline-start': theme('spacing.5') },
        '.ms-6': { 'margin-inline-start': theme('spacing.6') },
        '.me-1': { 'margin-inline-end': theme('spacing.1') },
        '.me-2': { 'margin-inline-end': theme('spacing.2') },
        '.me-3': { 'margin-inline-end': theme('spacing.3') },
        '.me-4': { 'margin-inline-end': theme('spacing.4') },
        '.me-5': { 'margin-inline-end': theme('spacing.5') },
        '.me-6': { 'margin-inline-end': theme('spacing.6') },
      })
      
      // Focus-visible utilities for better accessibility
      addUtilities({
        '.focus-visible-ring': {
          '&:focus-visible': {
            outline: '2px solid transparent',
            'outline-offset': '2px',
            'box-shadow': '0 0 0 2px hsl(var(--ring))',
          },
        },
        '.focus-visible-ring-offset': {
          '&:focus-visible': {
            outline: '2px solid transparent',
            'outline-offset': '2px',
            'box-shadow': '0 0 0 2px hsl(var(--background)), 0 0 0 4px hsl(var(--ring))',
          },
        },
      })
      
      // High contrast mode utilities
      addUtilities({
        '.high-contrast': {
          '@media (prefers-contrast: high)': {
            'border-width': '2px',
            'font-weight': '600',
          },
        },
      })
      
      // Reduced motion utilities
      addUtilities({
        '.motion-safe': {
          '@media (prefers-reduced-motion: no-preference)': {
            'animation-duration': 'var(--animation-duration, 0.3s)',
          },
          '@media (prefers-reduced-motion: reduce)': {
            'animation-duration': '0.01ms',
            'animation-iteration-count': '1',
            'transition-duration': '0.01ms',
          },
        },
      })
    },
  ],
}