import { supabase } from '@/lib/supabase'
import { WoKendari } from '@/lib/types'

export async function toggleBookmark(
  table: string,
  ticket: WoKendari,
  currentUser: string
): Promise<{ error: string | null }> {
  // sudah di-bookmark orang lain -> tidak boleh diubah user ini
  if (ticket.bookmarked_by && ticket.bookmarked_by !== currentUser) {
    return { error: `Tiket ini sudah dibookmark oleh ${ticket.bookmarked_by}.` }
  }

  const isOwnBookmark = ticket.bookmarked_by === currentUser

  const { error } = await supabase
    .from(table)
    .update(
      isOwnBookmark
        ? { bookmarked_by: null, bookmarked_at: null } // lepas bookmark
        : { bookmarked_by: currentUser, bookmarked_at: new Date().toISOString() } // pasang bookmark
    )
    .eq('id', ticket.id)

  return { error: error?.message ?? null }
}