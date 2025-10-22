import React, { createContext, useContext, useState, useCallback } from 'react'

interface LoadingState {
  global: boolean
  operations: Record<string, boolean>
}

interface LoadingContextType {
  isLoading: boolean
  isOperationLoading: (operation: string) => boolean
  setGlobalLoading: (loading: boolean) => void
  setOperationLoading: (operation: string, loading: boolean) => void
  withLoading: <T>(operation: string, fn: () => Promise<T>) => Promise<T>
  withGlobalLoading: <T>(fn: () => Promise<T>) => Promise<T>
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined)

export function LoadingProvider({ children }: { children: React.ReactNode }) {
  const [loadingState, setLoadingState] = useState<LoadingState>({
    global: false,
    operations: {},
  })

  const setGlobalLoading = useCallback((loading: boolean) => {
    setLoadingState(prev => ({ ...prev, global: loading }))
  }, [])

  const setOperationLoading = useCallback((operation: string, loading: boolean) => {
    setLoadingState(prev => ({
      ...prev,
      operations: {
        ...prev.operations,
        [operation]: loading,
      },
    }))
  }, [])

  const isOperationLoading = useCallback((operation: string) => {
    return Boolean(loadingState.operations[operation])
  }, [loadingState.operations])

  const withLoading = useCallback(async <T,>(
    operation: string,
    fn: () => Promise<T>
  ): Promise<T> => {
    setOperationLoading(operation, true)
    try {
      return await fn()
    } finally {
      setOperationLoading(operation, false)
    }
  }, [setOperationLoading])

  const withGlobalLoading = useCallback(async <T,>(
    fn: () => Promise<T>
  ): Promise<T> => {
    setGlobalLoading(true)
    try {
      return await fn()
    } finally {
      setGlobalLoading(false)
    }
  }, [setGlobalLoading])

  const isLoading = loadingState.global || Object.values(loadingState.operations).some(Boolean)

  const value: LoadingContextType = {
    isLoading,
    isOperationLoading,
    setGlobalLoading,
    setOperationLoading,
    withLoading,
    withGlobalLoading,
  }

  return (
    <LoadingContext.Provider value={value}>
      {children}
    </LoadingContext.Provider>
  )
}

export function useLoading() {
  const context = useContext(LoadingContext)
  if (context === undefined) {
    throw new Error('useLoading must be used within a LoadingProvider')
  }
  return context
}

// Specific hooks for common operations
export function useOperationLoading(operation: string) {
  const { isOperationLoading, setOperationLoading, withLoading } = useLoading()
  
  return {
    isLoading: isOperationLoading(operation),
    setLoading: (loading: boolean) => setOperationLoading(operation, loading),
    withLoading: <T,>(fn: () => Promise<T>) => withLoading(operation, fn),
  }
}

export function useGlobalLoading() {
  const { isLoading, setGlobalLoading, withGlobalLoading } = useLoading()
  
  return {
    isLoading,
    setLoading: setGlobalLoading,
    withLoading: withGlobalLoading,
  }
}