// lib/syncKendala.ts
import { SupabaseClient } from '@supabase/supabase-js';

const KOTA_RPC_MAP: Record<string, string> = {
  kendari: 'sync_kendala_kendari',
  kolaka: 'sync_kendala_kolaka',
  baubau: 'sync_kendala_baubau',
};

export async function syncKendalaForKota(
  supabase: SupabaseClient,
  kota: keyof typeof KOTA_RPC_MAP
) {
  const rpcName = KOTA_RPC_MAP[kota];
  const { error } = await supabase.rpc(rpcName);
  if (error) throw error;
}