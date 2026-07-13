import { useState, useEffect, useCallback, useRef } from 'react'
import { lookupCnpj, getOwnershipTree } from '../utils/api'

/**
 * Custom hook for CNPJ company lookup
 * @param {string} cnpj - CNPJ to look up
 * @returns {{ data, loading, error, refetch }}
 */
export function useCnpjLookup(cnpj) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const fetchData = useCallback(async () => {
    if (!cnpj) return

    // Cancel previous request
    if (abortRef.current) {
      abortRef.current.abort()
    }

    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError(null)

    try {
      const result = await lookupCnpj(cnpj)
      if (!controller.signal.aborted) {
        setData(result)
        setLoading(false)
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err)
        setLoading(false)
      }
    }
  }, [cnpj])

  useEffect(() => {
    setData(null)
    setError(null)
    fetchData()

    return () => {
      if (abortRef.current) {
        abortRef.current.abort()
      }
    }
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}

/**
 * Custom hook for ownership tree
 * Fetches when cnpj changes and hasPjPartners is true, or when refetch is called
 * @param {string} cnpj - CNPJ to look up
 * @param {boolean} shouldFetch - whether to auto-fetch (e.g. has PJ partners)
 * @returns {{ data, loading, error, refetch }}
 */
export function useOwnershipTree(cnpj, shouldFetch = false) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)
  const hasFetchedRef = useRef(false)

  const fetchData = useCallback(async () => {
    if (!cnpj) return

    if (abortRef.current) {
      abortRef.current.abort()
    }

    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError(null)

    try {
      const result = await getOwnershipTree(cnpj)
      if (!controller.signal.aborted) {
        setData(result)
        setLoading(false)
        hasFetchedRef.current = true
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err)
        setLoading(false)
      }
    }
  }, [cnpj])

  useEffect(() => {
    // Reset on cnpj change
    setData(null)
    setError(null)
    hasFetchedRef.current = false
  }, [cnpj])

  useEffect(() => {
    if (shouldFetch && cnpj && !hasFetchedRef.current) {
      fetchData()
    }

    return () => {
      if (abortRef.current) {
        abortRef.current.abort()
      }
    }
  }, [shouldFetch, cnpj, fetchData])

  return { data, loading, error, refetch: fetchData }
}
