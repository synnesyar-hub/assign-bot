import { supabase } from '@/lib/supabase'
import { WoKendari } from '@/lib/types'

export async function toggleDelete(table: string, item: WoKendari) {
  const newVal = !item.is_deleted
  const { error } = await supabase
    .from(table)
    .update({
      is_deleted: newVal,
      deleted_at: newVal ? new Date().toISOString() : null,
    })
    .eq('id', item.id)

  return { error }
}