/* assign-bot/wo-kendari-dashboard/components/WoFilters.tsx */

'use client'

import { WoStatus, SortOption, SORT_OPTIONS } from '@/lib/types'

const ALL_STATUSES: WoStatus[] = [
  'OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING', 'CLOSE CROSSCHECK', 'CLOSE',
]

interface Props {
  search: string
  onSearchChange: (v: string) => void
  statusFilter: WoStatus | 'ALL'
  onStatusFilterChange: (v: WoStatus | 'ALL') => void
  areaOptions: string[]
  areaFilter: string
  onAreaFilterChange: (v: string) => void
  rayonOptions: string[]
  rayonFilter: string
  onRayonFilterChange: (v: string) => void
  sortOption: SortOption
  onSortOptionChange: (v: SortOption) => void
}

export default function WoFilters({
  search, onSearchChange,
  statusFilter, onStatusFilterChange,
  areaOptions, areaFilter, onAreaFilterChange,
  rayonOptions, rayonFilter, onRayonFilterChange,
  sortOption, onSortOptionChange,
}: Props) {
  const sortValue = `${sortOption.key}:${sortOption.dir}`

  const handleSortChange = (value: string) => {
    const found = SORT_OPTIONS.find((o) => `${o.key}:${o.dir}` === value)
    if (found) onSortOptionChange(found)
  }

  return (
    <div className="mb-4 flex flex-col gap-3">
      <input
        type="text"
        placeholder="Cari incident / nama pelanggan..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm placeholder:text-gray-400 focus:border-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-300 sm:max-w-xs"
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value as WoStatus | 'ALL')}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm focus:border-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-300"
        >
          <option value="ALL">Semua Status</option>
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select
          value={areaFilter}
          onChange={(e) => onAreaFilterChange(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm focus:border-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-300"
        >
          <option value="ALL">Semua Area</option>
          {areaOptions.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>

        <select
          value={rayonFilter}
          onChange={(e) => onRayonFilterChange(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm focus:border-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-300"
        >
          <option value="ALL">Semua Rayon</option>
          {rayonOptions.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>

        <select
          value={sortValue}
          onChange={(e) => handleSortChange(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm focus:border-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-300"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={`${o.key}:${o.dir}`} value={`${o.key}:${o.dir}`}>
              Urutkan: {o.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}