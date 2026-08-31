'use client'

import { useEffect, useState, useCallback } from 'react'
import { fetchTicketsFromTable } from './woService'
import { WoKendari, ALL_CITIES, CITY_TABLE } from './types'

export function useMultiCityTickets() {
  const [tickets, setTickets] = useState<WoKendari[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setIsLoading(true)
      const results = await Promise.all(
        ALL_CITIES.map((city) => fetchTicketsFromTable(CITY_TABLE[city]))
      )
      setTickets(results.flat())
      setError(null)
    } catch {
      setError('Gagal memuat data gabungan. Periksa koneksi Supabase.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return { tickets, isLoading, error }
}