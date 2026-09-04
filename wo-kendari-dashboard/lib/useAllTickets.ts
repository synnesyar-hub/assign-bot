// lib/useAllTickets.ts
'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from './supabase'
import { fetchTicketsFromTable, updateTicketStatusInTable } from './woService'
import { WoKendari, WoStatus, CITY_TABLE, ALL_CITIES, CityKey } from './types'

export interface WoTicketWithCity extends WoKendari {
  _kota: CityKey
}

const REALTIME_DEBOUNCE_MS = 800

export function useAllTickets() {
  const [tickets, setTickets] = useState<WoTicketWithCity[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isUnmountedRef = useRef(false)
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

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

  // Event Realtime yang datang bertubi-tubi (mis. saat batch upsert ratusan baris)
  // digabung jadi satu refetch saja, supaya tidak membanjiri koneksi browser.
  const scheduleLoad = useCallback(() => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
    debounceTimerRef.current = setTimeout(() => {
      debounceTimerRef.current = null
      if (!isUnmountedRef.current) load()
    }, REALTIME_DEBOUNCE_MS)
  }, [load])

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
              scheduleLoad()
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
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
      channels.forEach((ch) => supabase.removeChannel(ch))
    }
  }, [load, scheduleLoad])

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