import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { cn } from '@/lib/utils'

interface ProgressBarProps {
  className?: string
  height?: number
  color?: string
  delay?: number
}

export function ProgressBar({ 
  className, 
  height = 3, 
  color = 'hsl(var(--primary))', 
  delay = 0 
}: ProgressBarProps) {
  const router = useRouter()
  const [progress, setProgress] = useState(0)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    let timer: NodeJS.Timeout

    const handleStart = () => {
      if (delay > 0) {
        timer = setTimeout(() => {
          setIsVisible(true)
          setProgress(0)
        }, delay)
      } else {
        setIsVisible(true)
        setProgress(0)
      }
    }

    const handleComplete = () => {
      if (timer) clearTimeout(timer)
      setProgress(100)
      setTimeout(() => {
        setIsVisible(false)
        setProgress(0)
      }, 300)
    }

    const handleError = () => {
      if (timer) clearTimeout(timer)
      setIsVisible(false)
      setProgress(0)
    }

    router.events.on('routeChangeStart', handleStart)
    router.events.on('routeChangeComplete', handleComplete)
    router.events.on('routeChangeError', handleError)

    return () => {
      if (timer) clearTimeout(timer)
      router.events.off('routeChangeStart', handleStart)
      router.events.off('routeChangeComplete', handleComplete)
      router.events.off('routeChangeError', handleError)
    }
  }, [router.events, delay])

  // Animate progress when visible
  useEffect(() => {
    if (!isVisible) return

    const timer = setTimeout(() => {
      setProgress(prev => {
        if (prev >= 95) return prev
        const increment = Math.random() * 10 + 5
        return Math.min(prev + increment, 95)
      })
    }, 200)

    return () => clearTimeout(timer)
  }, [isVisible, progress])

  if (!isVisible) return null

  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transform-gpu',
        className
      )}
      style={{ height: `${height}px` }}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Page loading progress"
    >
      <div
        className="h-full transition-all duration-300 ease-out"
        style={{
          width: `${progress}%`,
          backgroundColor: color,
          boxShadow: `0 0 10px ${color}`,
        }}
      />
    </div>
  )
}