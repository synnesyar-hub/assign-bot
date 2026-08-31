import { useRef, useCallback } from 'react'
import { supabase } from '@/lib/supabase'

export function useDebouncedSave(table: string, onSaved?: () => void, delayMs = 800) {
  const timers = useRef<Record<string, NodeJS.Timeout>>({})

  const save = useCallback(
    (id: number, column: string, value: string, updatedBy: string) => {
      const key = `${id}-${column}`
      if (timers.current[key]) clearTimeout(timers.current[key])

      timers.current[key] = setTimeout(async () => {
        await supabase
          .from(table)
          .update({ [column]: value, updated_by: updatedBy, updated_at: new Date().toISOString() })
          .eq('id', id)
        onSaved?.()
      }, delayMs)
    },
    [table, delayMs, onSaved]
  )

  return save
}