'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from './supabase'
import { fetchTicketsFromTable, updateTicketStatusInTable } from './woService'
import { WoKendari, WoStatus } from './types'

export function useTickets(table: string) {
  const [tickets, setTickets] = useState<WoKendari[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isUnmountedRef = useRef(false)

  const load = useCallback(async () => {
    try {
      setIsLoading(true)
      const data = await fetchTicketsFromTable(table)
      setTickets(data)
      setError(null)
    } catch {
      setError('Gagal memuat data tiket. Periksa koneksi Supabase.')
    } finally {
      setIsLoading(false)
    }
  }, [table])

  useEffect(() => {
    isUnmountedRef.current = false
    load()

    let channel: ReturnType<typeof supabase.channel>

    const setupChannel = () => {
      channel = supabase
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
            // koneksi realtime putus -> sambung ulang otomatis
            setTimeout(setupChannel, 1000)
          }
        })
    }

    setupChannel()

    return () => {
      isUnmountedRef.current = true
      supabase.removeChannel(channel)
    }
  }, [table, load])

  async function changeStatus(id: number, status: WoStatus) {
    const prev = tickets
    setTickets((cur) => cur.map((t) => (t.id === id ? { ...t, status } : t)))
    try {
      await updateTicketStatusInTable(table, id, status)
    } catch {
      setTickets(prev)
    }
  }

  return { tickets, isLoading, error, changeStatus }
}