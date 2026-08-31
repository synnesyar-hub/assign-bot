import { supabase } from './supabase'
import { WoKendari, WoStatus } from './types'

export async function fetchTicketsFromTable(table: string): Promise<WoKendari[]> {
  const { data, error } = await supabase
    .from(table)
    .select('*')
    .order('status_order', { ascending: true })

  if (error) {
    console.error(`fetchTicketsFromTable(${table}) error:`, error.message)
    throw error
  }
  return data as WoKendari[]
}

export async function updateTicketStatusInTable(
  table: string,
  id: number,
  status: WoStatus
): Promise<void> {
  const { error } = await supabase
    .from(table)
    .update({ status, updated_at: new Date().toISOString() })
    .eq('id', id)

  if (error) {
    console.error(`updateTicketStatusInTable(${table}) error:`, error.message)
    throw error
  }
}