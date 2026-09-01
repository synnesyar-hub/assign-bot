// lib/syncKendala.ts
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { computeKendala } from './computeKendala';

const KOTA_TABLE_MAP: Record<string, string> = {
  kendari: 'wo_kendari',
  kolaka: 'wo_kolaka',
  baubau: 'wo_baubau',
};

interface RawTicketRow {
  incident: string | null;
  onu_rx: string | number | null;
  symptom: string | null;
  gaul: string | number | null;
}

interface WoIncidentRow {
  incident: string | null;
}

export async function syncKendalaForKota(
  supabase: SupabaseClient,
  kota: keyof typeof KOTA_TABLE_MAP
) {
  const targetTable = KOTA_TABLE_MAP[kota];

  const { data: woRows, error: woErr } = await supabase
    .from(targetTable)
    .select('incident')
    .returns<WoIncidentRow[]>();
  if (woErr) throw woErr;

  const incidentIds = (woRows ?? [])
    .map((r) => r.incident)
    .filter((id): id is string => !!id);

  if (incidentIds.length === 0) return;

  const [db1, db2] = await Promise.all([
    supabase
      .from('tickets_database')
      .select('incident, onu_rx, symptom, gaul')
      .in('incident', incidentIds)
      .returns<RawTicketRow[]>(),
    supabase
      .from('tickets_database2')
      .select('incident, onu_rx, symptom, gaul')
      .in('incident', incidentIds)
      .returns<RawTicketRow[]>(),
  ]);
  if (db1.error) throw db1.error;
  if (db2.error) throw db2.error;

  const rawRows: RawTicketRow[] = [...(db1.data ?? []), ...(db2.data ?? [])];

  const updates = rawRows
    .filter((r): r is RawTicketRow & { incident: string } => !!r.incident)
    .map((r) => ({
      incident: r.incident,
      kendala: computeKendala(r.onu_rx, r.symptom, r.gaul),
    }));

  if (updates.length === 0) return;

  for (const u of updates) {
    const { error } = await supabase
      .from(targetTable)
      .update({ kendala: u.kendala })
      .eq('incident', u.incident);
    if (error) throw error;
  }
}