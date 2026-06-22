"use client"

import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react'

interface ComponentAnalysis {
  id: string
  name: string
  type: string
  criticality_level: string
  criticality_levels?: {
    reliability: string
    maintainability: string
    availability: string
    security: string
    overall: string
  }
  scores: {
    reliability: number
    maintainability: number
    availability: number
    security: number
    overall: number
  }
}

interface EdgeAnalysis {
  source: string
  target: string
  source_name?: string
  target_name?: string
  type: string
  criticality_level: string
  scores: {
    reliability: number
    maintainability: number
    availability: number
    security: number
    overall: number
  }
}

interface Problem {
  entity_id: string
  type: string
  category: string
  severity: string
  name: string
  description: string
  recommendation: string
}

interface AnalysisResult {
  context?: string
  description?: string
  summary: any
  stats: any
  components: ComponentAnalysis[]
  edges?: EdgeAnalysis[]
  problems: Problem[]
  logs?: string[]
}

interface AnalysisState {
  cache: Record<string, AnalysisResult>
}

interface AnalysisContextType extends AnalysisState {
  setAnalysis: (key: string, result: AnalysisResult) => void
  getAnalysis: (key: string) => AnalysisResult | null
  clearAnalysis: (key?: string) => void
  clearAll: () => void
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined)

const STORAGE_KEY = 'analysis-cache'
const CACHE_VERSION = 3
const MAX_CACHE_ITEMS = 4

const getStorage = (): Storage | null => {
  if (typeof window === 'undefined') return null
  return window.localStorage
}

const compressTier = (result: AnalysisResult, tier: number): AnalysisResult => {
  const base: AnalysisResult = {
    context: result.context,
    description: result.description,
    summary: result.summary,
    stats: result.stats,
    components: result.components || [],
    edges: result.edges || [],
    problems: result.problems || [],
    logs: result.logs || [],
  }

  if (tier <= 0) return base

  const stripped = { ...base, logs: [] as string[] }

  if (tier <= 1) return stripped

  const noEdgeDetails: AnalysisResult = {
    ...stripped,
    edges: (stripped.edges || []).map(e => ({
      source: e.source,
      target: e.target,
      type: e.type,
      criticality_level: e.criticality_level,
      scores: e.scores,
    })),
  }

  if (tier <= 2) return noEdgeDetails

  const slimComponents = noEdgeDetails.components.map(c => ({
    id: c.id,
    name: c.name,
    type: c.type,
    criticality_level: c.criticality_level,
    scores: c.scores,
  }))
  const slimEdges = (noEdgeDetails.edges || []).map(e => ({
    source: e.source,
    target: e.target,
    type: e.type,
    criticality_level: e.criticality_level,
    scores: e.scores,
  }))
  const slimProblems = noEdgeDetails.problems.map(p => ({
    entity_id: p.entity_id,
    type: p.type,
    category: p.category,
    severity: p.severity,
    name: p.name,
    description: p.description || '',
    recommendation: p.recommendation || '',
  }))

  const slim: AnalysisResult = {
    ...noEdgeDetails,
    components: slimComponents,
    edges: slimEdges,
    problems: slimProblems,
  }

  if (tier <= 3) return slim

  const maxItems = Math.max(50, Math.floor(500 / Math.pow(2, tier - 3)))
  return {
    ...slim,
    components: slim.components.slice(0, maxItems),
    edges: (slim.edges || []).slice(0, maxItems),
    problems: slim.problems.slice(0, maxItems),
  }
}

const MAX_TIERS = 6

const saveToStorage = (cache: Record<string, AnalysisResult>) => {
  const storage = getStorage()
  if (!storage) return

  const keys = Object.keys(cache)
  const trimmedCache: Record<string, AnalysisResult> = {}
  const keysToKeep = keys.length > MAX_CACHE_ITEMS ? keys.slice(-MAX_CACHE_ITEMS) : keys
  keysToKeep.forEach(key => { trimmedCache[key] = cache[key] })

  const tryWrite = (payload: object) => {
    storage.setItem(STORAGE_KEY, JSON.stringify({ v: CACHE_VERSION, data: payload }))
  }

  try {
    tryWrite(trimmedCache)
    return
  } catch (e: any) {
    if (e.name !== 'QuotaExceededError') {
      console.error('Failed to save analysis cache:', e)
      return
    }
  }

  for (let tier = 1; tier <= MAX_TIERS; tier++) {
    try {
      const degraded: Record<string, AnalysisResult> = {}
      Object.entries(trimmedCache).forEach(([k, v]) => {
        degraded[k] = compressTier(v, tier)
      })
      tryWrite(degraded)
      return
    } catch {
      continue
    }
  }

  console.warn('Storage quota exceeded at all compression tiers; cache not persisted')
}

const loadFromStorage = (): Record<string, AnalysisResult> => {
  const storage = getStorage()
  if (!storage) return {}

  try {
    const saved = storage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (parsed.v !== CACHE_VERSION) {
        storage.removeItem(STORAGE_KEY)
        return {}
      }
      return parsed.data as Record<string, AnalysisResult>
    }
  } catch (error) {
    console.error('Failed to load analysis cache:', error)
    storage.removeItem(STORAGE_KEY)
  }
  return {}
}

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AnalysisState>({
    cache: {}
  })
  const pendingSaveRef = useRef<Record<string, AnalysisResult> | null>(null)

  useEffect(() => {
    const loadedCache = loadFromStorage()
    if (Object.keys(loadedCache).length > 0) {
      setState(prev => ({ ...prev, cache: loadedCache }))
    }
  }, [])

  useEffect(() => {
    if (pendingSaveRef.current) {
      saveToStorage(pendingSaveRef.current)
      pendingSaveRef.current = null
    }
  }, [state.cache])

  const setAnalysis = (key: string, result: AnalysisResult) => {
    setState(prev => {
      const newCache = {
        ...prev.cache,
        [key]: compressTier(result, 0)
      }
      pendingSaveRef.current = newCache
      return { ...prev, cache: newCache }
    })
  }

  const getAnalysis = (key: string): AnalysisResult | null => {
    return state.cache[key] || null
  }

  const clearAnalysis = (key?: string) => {
    if (key) {
      setState(prev => {
        const newCache = { ...prev.cache }
        delete newCache[key]
        pendingSaveRef.current = newCache
        return { ...prev, cache: newCache }
      })
    } else {
      setState({ cache: {} })
      pendingSaveRef.current = null
      const storage = getStorage()
      if (storage) storage.removeItem(STORAGE_KEY)
    }
  }

  const clearAll = () => {
    setState({ cache: {} })
    pendingSaveRef.current = null
    const storage = getStorage()
    if (storage) storage.removeItem(STORAGE_KEY)
  }

  return (
    <AnalysisContext.Provider
      value={{
        ...state,
        setAnalysis,
        getAnalysis,
        clearAnalysis,
        clearAll
      }}
    >
      {children}
    </AnalysisContext.Provider>
  )
}

export function useAnalysis() {
  const context = useContext(AnalysisContext)
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider')
  }
  return context
}
