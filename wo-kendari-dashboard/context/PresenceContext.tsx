'use client'

import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react'
import { RealtimeChannel } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { EditingPresence } from '@/types/presence'
import { useCurrentUser } from '@/lib/useCurrentUser'

interface PresenceContextValue {
  presenceState: Record<string, EditingPresence[]>
  setEditing: (ticketId: string | null, column: string | null) => void
}

const PresenceContext = createContext<PresenceContextValue | null>(null)

export function PresenceProvider({ children }: { children: ReactNode }) {
  const currentUser = useCurrentUser()
  const channelRef = useRef<RealtimeChannel | null>(null)
  const [presenceState, setPresenceState] = useState<Record<string, EditingPresence[]>>({})

  useEffect(() => {
    if (!currentUser) return

    let channel: RealtimeChannel
    let isUnmounted = false

    const setupChannel = () => {
      channel = supabase.channel('global-editing', {
        config: { presence: { key: currentUser } },
      })

      channel
        .on('presence', { event: 'sync' }, () => {
          setPresenceState(channel.presenceState() as Record<string, EditingPresence[]>)
        })
        .subscribe(async (status) => {
          if (status === 'SUBSCRIBED') {
            await channel.track({ user: currentUser, ticketId: null, column: null, at: null })
          }
          if (
            (status === 'CLOSED' || status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') &&
            !isUnmounted
          ) {
            setTimeout(setupChannel, 1000)
          }
        })

      channelRef.current = channel
    }

    setupChannel()

    return () => {
      isUnmounted = true
      channel?.unsubscribe()
      channelRef.current = null
    }
  }, [currentUser])

  const setEditing = (ticketId: string | null, column: string | null) => {
    channelRef.current?.track({
      user: currentUser,
      ticketId,
      column,
      at: ticketId ? new Date().toISOString() : null,
    })
  }

  return (
    <PresenceContext.Provider value={{ presenceState, setEditing }}>
      {children}
    </PresenceContext.Provider>
  )
}

export function usePresence() {
  const ctx = useContext(PresenceContext)
  if (!ctx) throw new Error('usePresence harus dipakai di dalam PresenceProvider')
  return ctx
}