/**
 * Theme Provider Component
 * 
 * Provides theme context using next-themes for dark/light mode switching
 */

'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import type { ThemeProviderProps } from 'next-themes/dist/types'

interface ThemeContextType {
  theme: string | undefined
  setTheme: (theme: string) => void
  systemTheme: string | undefined
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  
  // If we're not in our custom context, fall back to next-themes
  if (!context) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { theme, setTheme, systemTheme } = require('next-themes').useTheme()
    return { theme, setTheme, systemTheme }
  }
  
  return context
}

export default ThemeProvider