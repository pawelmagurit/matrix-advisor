import { useCallback, useEffect, useState } from 'react'
import type { CutSessionConfig, MatrixInfo, OrderLine } from '@/lib/cutting/types'
import {
  EXTRAL_SAMPLE_CONFIG,
  EXTRAL_SAMPLE_MATRIX,
  EXTRAL_SAMPLE_ORDERS,
  loadExtralSample,
} from '@/data/extral-sample'

const ORDERS_KEY = 'cut-planner-orders'
const CONFIG_KEY = 'cut-planner-config'
const MATRIX_KEY = 'cut-planner-matrix'

function loadOrders(): OrderLine[] {
  try {
    const raw = localStorage.getItem(ORDERS_KEY)
    if (raw) return JSON.parse(raw) as OrderLine[]
  } catch {
    /* ignore */
  }
  return []
}

function loadConfig(): CutSessionConfig {
  try {
    const raw = localStorage.getItem(CONFIG_KEY)
    if (raw) return JSON.parse(raw) as CutSessionConfig
  } catch {
    /* ignore */
  }
  return { ...EXTRAL_SAMPLE_CONFIG }
}

function loadMatrixInfo(): MatrixInfo | null {
  try {
    const raw = localStorage.getItem(MATRIX_KEY)
    if (raw) return JSON.parse(raw) as MatrixInfo
  } catch {
    /* ignore */
  }
  return null
}

export function useCutPlannerState() {
  const [orders, setOrders] = useState<OrderLine[]>(loadOrders)
  const [config, setConfig] = useState<CutSessionConfig>(loadConfig)
  const [matrixInfo, setMatrixInfo] = useState<MatrixInfo | null>(loadMatrixInfo)

  useEffect(() => {
    localStorage.setItem(ORDERS_KEY, JSON.stringify(orders))
  }, [orders])

  useEffect(() => {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config))
  }, [config])

  useEffect(() => {
    if (matrixInfo) {
      localStorage.setItem(MATRIX_KEY, JSON.stringify(matrixInfo))
    } else {
      localStorage.removeItem(MATRIX_KEY)
    }
  }, [matrixInfo])

  const loadSample = useCallback(() => {
    const sample = loadExtralSample()
    setOrders(sample.orders)
    setConfig(sample.config)
    setMatrixInfo(sample.matrixInfo)
  }, [])

  const clearMatrixInfo = useCallback(() => {
    setMatrixInfo(null)
  }, [])

  return {
    orders,
    setOrders,
    config,
    setConfig,
    matrixInfo,
    setMatrixInfo,
    loadSample,
    clearMatrixInfo,
    /** Domyślne wartości sample — do eksportu CSV bez wczytywania do stanu */
    sampleOrders: EXTRAL_SAMPLE_ORDERS,
    sampleMatrix: EXTRAL_SAMPLE_MATRIX,
  }
}
