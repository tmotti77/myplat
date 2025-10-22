/**
 * Simple Accessibility Menu - Working Version
 */

import { useState } from 'react'
import { useTranslation } from 'next-i18next'
import {
  Settings,
  Eye,
  Type,
  Contrast,
  Volume2,
  X
} from 'lucide-react'

interface AccessibilityMenuProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AccessibilityMenu({ open, onOpenChange }: AccessibilityMenuProps) {
  const { t } = useTranslation('common')
  const [settings, setSettings] = useState({
    largeText: false,
    highContrast: false,
    reduceMotion: false,
    screenReader: false
  })

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold flex items-center">
            <Settings className="mr-2" size={20} />
            Accessibility Settings
          </h2>
          <button
            onClick={() => onOpenChange(false)}
            className="p-1 rounded hover:bg-gray-100"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Type className="mr-2" size={16} />
              <span>Large Text</span>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, largeText: !prev.largeText }))}
              className={`w-12 h-6 rounded-full ${settings.largeText ? 'bg-blue-600' : 'bg-gray-300'} relative transition-colors`}
            >
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${settings.largeText ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Contrast className="mr-2" size={16} />
              <span>High Contrast</span>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, highContrast: !prev.highContrast }))}
              className={`w-12 h-6 rounded-full ${settings.highContrast ? 'bg-blue-600' : 'bg-gray-300'} relative transition-colors`}
            >
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${settings.highContrast ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Eye className="mr-2" size={16} />
              <span>Reduce Motion</span>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, reduceMotion: !prev.reduceMotion }))}
              className={`w-12 h-6 rounded-full ${settings.reduceMotion ? 'bg-blue-600' : 'bg-gray-300'} relative transition-colors`}
            >
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${settings.reduceMotion ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Volume2 className="mr-2" size={16} />
              <span>Screen Reader</span>
            </div>
            <button
              onClick={() => setSettings(prev => ({ ...prev, screenReader: !prev.screenReader }))}
              className={`w-12 h-6 rounded-full ${settings.screenReader ? 'bg-blue-600' : 'bg-gray-300'} relative transition-colors`}
            >
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${settings.screenReader ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t">
          <button
            onClick={() => onOpenChange(false)}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Apply Settings
          </button>
        </div>
      </div>
    </div>
  )
}