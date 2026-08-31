import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'

export function usePins(userId: string, city: string) {
  const [pinnedIds, setPinnedIds] = useState<Set<number>>(new Set())

  const fetchPins = useCallback(async () => {
    if (!userId) return
    const { data } = await supabase
      .from('user_pins')
      .select('ticket_id')
      .eq('user_id', userId)
      .eq('city', city)

    setPinnedIds(new Set((data ?? []).map((row) => row.ticket_id)))
  }, [userId, city])

  useEffect(() => {
    fetchPins()
  }, [fetchPins])

  const togglePin = async (ticketId: number) => {
    const isPinned = pinnedIds.has(ticketId)

    if (isPinned) {
      await supabase
        .from('user_pins')
        .delete()
        .eq('user_id', userId)
        .eq('ticket_id', ticketId)
        .eq('city', city)
    } else {
      await supabase
        .from('user_pins')
        .insert({ user_id: userId, ticket_id: ticketId, city })
    }

    setPinnedIds((prev) => {
      const next = new Set(prev)
      isPinned ? next.delete(ticketId) : next.add(ticketId)
      return next
    })
  }

  return { pinnedIds, togglePin }
}