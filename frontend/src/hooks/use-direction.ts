import { useMemo } from 'react'

// Languages that use RTL writing direction
const RTL_LANGUAGES = [
  'ar', // Arabic
  'he', // Hebrew
  'fa', // Persian/Farsi
  'ur', // Urdu
  'yi', // Yiddish
  'iw', // Hebrew (legacy code)
  'ji', // Yiddish (legacy code)
  'arc', // Aramaic
  'dv', // Divehi
  'ku', // Kurdish (Sorani)
  'ps', // Pashto
  'sd', // Sindhi
  'ug', // Uyghur
]

export function useDirection(locale?: string): 'ltr' | 'rtl' {
  return useMemo(() => {
    if (!locale) return 'ltr'
    
    // Extract language code from locale (e.g., 'en-US' -> 'en')
    const language = locale.split('-')[0].toLowerCase()
    
    return RTL_LANGUAGES.includes(language) ? 'rtl' : 'ltr'
  }, [locale])
}

export default useDirection