// lib/useAllTickets.ts
'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from './supabase'
import { fetchTicketsFromTable, updateTicketStatusInTable } from './woService'
import { WoKendari, WoStatus, CITY_TABLE, ALL_CITIES, CityKey } from './types'

export interface WoTicketWithCity extends WoKendari {
  _kota: CityKey
}

export function useAllTickets() {
  const [tickets, setTickets] = useState<WoTicketWithCity[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isUnmountedRef = useRef(false)

  const load = useCallback(async () => {
    try {
      setIsLoading(true)
      const results = await Promise.all(
        ALL_CITIES.map(async (kota) => {
          const data = await fetchTicketsFromTable(CITY_TABLE[kota])
          return data.map((row) => ({ ...row, _kota: kota })) as WoTicketWithCity[]
        })
      )
      setTickets(results.flat())
      setError(null)
    } catch {
      setError('Gagal memuat data tiket. Periksa koneksi Supabase.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    isUnmountedRef.current = false
    load()

    let channels: ReturnType<typeof supabase.channel>[] = []

    const setupChannels = () => {
      channels = ALL_CITIES.map((kota) => {
        const table = CITY_TABLE[kota]
        return supabase
          .channel(`${table}_changes`)
          .on(
            'postgres_changes',
            { event: '*', schema: 'public', table },
            () => {
              load()
            }
          )
          .subscribe((status) => {
            if (
              (status === 'CLOSED' || status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') &&
              !isUnmountedRef.current
            ) {
              setTimeout(setupChannels, 1000)
            }
          })
      })
    }

    setupChannels()

    return () => {
      isUnmountedRef.current = true
      channels.forEach((ch) => supabase.removeChannel(ch))
    }
  }, [load])

  async function changeStatus(kota: CityKey, id: number, status: WoStatus) {
    const table = CITY_TABLE[kota]
    const prev = tickets
    setTickets((cur) => cur.map((t) => (t.id === id && t._kota === kota ? { ...t, status } : t)))
    try {
      await updateTicketStatusInTable(table, id, status)
    } catch {
      setTickets(prev)
    }
  }

  return { tickets, isLoading, error, changeStatus }
}