/* assign-bot/wo-kendari-dashboard/components/WoFilters.tsx */

'use client'

import { useState, useRef, useEffect } from 'react'
import { WoStatus } from '@/lib/types'

const ALL_STATUSES: WoStatus[] = [
  'OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING', 'CLOSE CROSSCHECK', 'CLOSE',
]

interface Props {
  search: string
  onSearchChange: (v: string) => void
  statusFilter: WoStatus | 'ALL'
  onStatusFilterChange: (v: WoStatus | 'ALL') => void
  areaOptions: string[]
  areaFilter: string[]
  onAreaFilterChange: (v: string[]) => void
  rayonOptions: string[]
  rayonFilter: string[]
  onRayonFilterChange: (v: string[]) => void
  sourceOptions: string[]           
  sourceFilter: string[]            
  onSourceFilterChange: (v: string[]) => void   
}

function MultiSelectDropdown({
  label,
  options,
  selected,
  onChange,
}: {
  label: string
  options: string[]
  selected: string[]
  onChange: (v: string[]) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleOption = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter((o) => o !== opt))
    } else {
      onChange([...selected, opt])
    }
  }

  const buttonLabel =
    selected.length === 0
      ? `Semua ${label}`
      : selected.length === 1
        ? selected[0]
        : `${selected.length} ${label} dipilih`

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex min-w-[160px] items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm hover:border-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-300"
      >
        <span className="truncate">{buttonLabel}</span>
        <span className="text-gray-400">▾</span>
      </button>

      {open && (
        <div className="absolute z-50 mt-1 max-h-80 w-64 overflow-y-auto rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
          {selected.length > 0 && (
            <button
              type="button"
              onClick={() => onChange([])}
              className="w-full px-4 py-2.5 text-left text-sm font-medium text-blue-600 hover:bg-gray-50"
            >
              Reset pilihan
            </button>
          )}
          {options.length === 0 && (
            <p className="px-4 py-3 text-sm text-gray-400">Tidak ada opsi</p>
          )}
          {options.map((opt) => (
            <label
              key={opt}
              className="flex cursor-pointer items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <input
                type="checkbox"
                checked={selected.includes(opt)}
                onChange={() => toggleOption(opt)}
                className="h-4 w-4 rounded border-gray-300 accent-blue-600"
              />
              {opt}
            </label>
          ))}
        </div>
      )}
    </div>
  )
}

export default function WoFilters({
  search, onSearchChange,
  statusFilter, onStatusFilterChange,
  areaOptions, areaFilter, onAreaFilterChange,
  rayonOptions, rayonFilter, onRayonFilterChange,
  sourceOptions, sourceFilter, onSourceFilterChange,
}: Props) {

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

        <MultiSelectDropdown label="Area" options={areaOptions} selected={areaFilter} onChange={onAreaFilterChange} />
        <MultiSelectDropdown label="Rayon" options={rayonOptions} selected={rayonFilter} onChange={onRayonFilterChange} />
        <MultiSelectDropdown label="Source" options={sourceOptions} selected={sourceFilter} onChange={onSourceFilterChange} />
      </div>
    </div>
  )
}