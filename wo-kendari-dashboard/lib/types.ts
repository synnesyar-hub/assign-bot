/* assign-bot/wo-kendari-dashboard/lib/types.ts */

export type WoStatus =
  | 'OPEN'
  | 'MONITORING'
  | 'GAMAS'
  | 'KENDALA'
  | 'PENDING'
  | 'CLOSE CROSSCHECK'
  | 'CLOSE'

export type CityKey = 'kendari' | 'kolaka' | 'baubau'

export const CITY_TABLE: Record<CityKey, string> = {
  kendari: 'wo_kendari',
  kolaka: 'wo_kolaka',
  baubau: 'wo_baubau',
}

export const CITY_SYNC_FN: Record<CityKey, string> = {
  kendari: 'sync_wo_kendari',
  kolaka: 'sync_wo_kolaka',
  baubau: 'sync_wo_baubau',
}

export const CITY_LABEL: Record<CityKey, string> = {
  kendari: 'Kendari',
  kolaka: 'Kolaka',
  baubau: 'Baubau',
}

export interface WoArchive extends WoKendari {
  kota: CityKey
}

export const ALL_CITIES: CityKey[] = ['kendari', 'kolaka', 'baubau']

export interface WoKendari {
  id: number
  incident: string
  source_worksheet: string

  // ===== AUTO (read-only di grid) =====
  reported_date: string | null
  customer_type: string | null
  customer_type_label: string | null
  service_no: string | null
  customer_name: string | null
  contact_phone: string | null
  source: string | null
  datek: string | null
  rayon: string | null
  sto: string | null
  odc: string | null
  service_area: string | null
  booking_date: string | null
  kendala: string | null

  // ===== MANUAL - CAMPUR TANGAN OPERATOR (editable) =====
  status: WoStatus
  status_order: number

  // ===== MANUAL PENUH (editable) =====
  teknisi: string | null
  perbaikan: string | null
  link_alamat: string | null
  kategori_ttr: string | null
  status_ttr: string | null
  job: string | null
  total: string | null

  created_at: string
  updated_at: string
  updated_by: string | null

  bookmarked_by: string | null
  bookmark_color: string | null
  bookmarked_at: string | null

  // ===== LOG (write-back sync ke Insera) =====
  log: string | null
  log_synced: boolean
  log_synced_at: string | null
  log_sync_error: string | null
  log_photo_path: string | null
  log_summary: string | null

  // ===== LAST LOG (AUTO, read-only — dari worklog_summary Insera) =====
  last_log: string | null

  // ===== SOFT DELETE =====
  is_deleted: boolean
  deleted_at: string | null
}

// Daftar kolom yang boleh diedit langsung di grid
export const EDITABLE_COLUMNS: (keyof WoKendari)[] = [
  'status',
  'teknisi',
  'perbaikan',
  'link_alamat',
  'kategori_ttr',
  'status_ttr',
  'job',
  'total',
]

export interface ColumnDef {
  key: keyof WoKendari | 'ttr' | 'ttr_manja'
  label: string
  editable: boolean
  type: 'text' | 'status' | 'date' | 'readonly' | 'ttr' | 'ttr_manja' | 'log'
  width?: string
}

export const COLUMN_DEFS: ColumnDef[] = [
  { key: 'reported_date', label: 'Tanggal Lapor', editable: false, type: 'date', width: 'min-w-[160px]' },
  { key: 'booking_date', label: 'Tgl Booking', editable: false, type: 'date', width: 'min-w-[160px]' },
  { key: 'customer_type_label', label: 'Tipe Pelanggan', editable: false, type: 'readonly', width: 'min-w-[120px]' },
  { key: 'incident', label: 'Incident', editable: false, type: 'readonly', width: 'min-w-[120px]' },
  { key: 'service_no', label: 'No. Layanan', editable: false, type: 'readonly', width: 'min-w-[120px]' },
  { key: 'customer_name', label: 'Nama Pelanggan', editable: false, type: 'readonly', width: 'min-w-[160px]' },
  { key: 'contact_phone', label: 'No. HP', editable: false, type: 'readonly', width: 'min-w-[120px]' },
  { key: 'source', label: 'Source', editable: false, type: 'readonly', width: 'min-w-[110px]' },
  { key: 'datek', label: 'Datek', editable: false, type: 'readonly', width: 'min-w-[100px]' },
  { key: 'kendala', label: 'Kendala', editable: false, type: 'readonly', width: 'min-w-[180px]' },
  { key: 'rayon', label: 'Rayon', editable: false, type: 'readonly', width: 'min-w-[120px]' },
  { key: 'ttr', label: 'TTR', editable: false, type: 'ttr', width: 'min-w-[110px]' },
  { key: 'ttr_manja', label: 'TTR Manja', editable: false, type: 'ttr_manja', width: 'min-w-[110px]' },
  { key: 'teknisi', label: 'Teknisi', editable: true, type: 'text', width: 'min-w-[120px]' },
  { key: 'status', label: 'Status', editable: true, type: 'status', width: 'min-w-[160px]' },
  { key: 'log', label: 'Log', editable: false, type: 'log', width: 'min-w-[220px]' },
  { key: 'last_log', label: 'Last Log', editable: false, type: 'readonly', width: 'min-w-[200px]' },
  { key: 'sto', label: 'STO', editable: false, type: 'readonly', width: 'min-w-[80px]' },
  { key: 'odc', label: 'ODC', editable: false, type: 'readonly', width: 'min-w-[100px]' },
  { key: 'service_area', label: 'Area Layanan', editable: false, type: 'readonly', width: 'min-w-[120px]' },
  { key: 'perbaikan', label: 'Perbaikan', editable: true, type: 'text', width: 'min-w-[180px]' },
  { key: 'link_alamat', label: 'Link Alamat', editable: true, type: 'text', width: 'min-w-[160px]' },
  { key: 'kategori_ttr', label: 'Kategori TTR', editable: true, type: 'text', width: 'min-w-[120px]' },
  { key: 'status_ttr', label: 'Status TTR', editable: true, type: 'text', width: 'min-w-[120px]' },
  { key: 'job', label: 'Job', editable: true, type: 'text', width: 'min-w-[100px]' },
  { key: 'total', label: 'Total', editable: true, type: 'text', width: 'min-w-[100px]' },
]

export interface SortOption {
  key: string
  dir: 'asc' | 'desc'
  label?: string
}

export const SORT_OPTIONS: SortOption[] = [
  { key: 'default', dir: 'asc', label: 'Default' },
  { key: 'reported_date', dir: 'desc', label: 'Tanggal Lapor (Terbaru)' },
  { key: 'reported_date', dir: 'asc', label: 'Tanggal Lapor (Terlama)' },
  { key: 'ttr', dir: 'desc', label: 'TTR (Tertinggi)' },
  { key: 'ttr', dir: 'asc', label: 'TTR (Terendah)' },
  { key: 'customer_name', dir: 'asc', label: 'Nama Pelanggan (A-Z)' },
  { key: 'customer_name', dir: 'desc', label: 'Nama Pelanggan (Z-A)' },
]

export const ALL_STATUSES: WoStatus[] = [
  'OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING', 'CLOSE CROSSCHECK', 'CLOSE',
]

export const ACTIVE_STATUSES: WoStatus[] = ['OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING']
export const INACTIVE_STATUSES: WoStatus[] = ['CLOSE CROSSCHECK', 'CLOSE']