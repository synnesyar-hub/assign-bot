/* components/WoTable.tsx */
'use client'

import { useState, useRef, useEffect } from 'react'
import EmptyState from '@/components/EmptyState'
import { WoKendari, COLUMN_DEFS, ACTIVE_STATUSES, SortOption } from '@/lib/types'
import { statusColor } from '@/lib/statusStyle'
import { formatTTR, formatManjaCountdown, getTTRColorClass, getTTRSeconds } from '@/lib/timeUtils'
import { useNow } from '@/lib/useNow'

const NON_SORTABLE_KEYS = ['status', 'ttr_manja']

const STICKY_KEYS = ['incident', 'reported_date', 'ttr', 'customer_type_label', 'service_no']
const STICKY_WIDTHS: Record<string, number> = {
  incident: 120,
  reported_date: 140,
  ttr: 110,
  customer_type_label: 120,
  service_no: 120,
}

function getStickyOffset(key: string): number | null {
  const idx = STICKY_KEYS.indexOf(key)
  if (idx === -1) return null
  return STICKY_KEYS.slice(0, idx).reduce((sum, k) => sum + STICKY_WIDTHS[k], 0)
}

function formatCell(value: unknown, type: string): string {
  if (value === null || value === undefined || value === '') return '-'
  if (type === 'date') {
    const d = new Date(value as string)
    if (isNaN(d.getTime())) return String(value)
    return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
  }
  return String(value)
}

function PinIconSmall() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" className="inline-block shrink-0 text-amber-500">
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M15.113 3.21l.094 .083l5.5 5.5a1 1 0 0 1 -1.175 1.59l-3.172 3.171l-1.424 3.797a1 1 0 0 1 -.158 .277l-.07 .08l-1.5 1.5a1 1 0 0 1 -1.32 .082l-.095 -.083l-2.793 -2.792l-3.793 3.792a1 1 0 0 1 -1.497 -1.32l.083 -.094l3.792 -3.793l-2.792 -2.793a1 1 0 0 1 -.083 -1.32l.083 -.094l1.5 -1.5a1 1 0 0 1 .258 -.187l.098 -.042l3.796 -1.425l3.171 -3.17a1 1 0 0 1 1.497 -1.26z" />
    </svg>
  )
}

function BookmarkIconSmall({ color }: { color: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={color} stroke="none" className="inline-block shrink-0">
      <path d="M17 3a2 2 0 0 1 2 2v15a1 1 0 0 1-1.496.868l-4.512-2.578a2 2 0 0 0-1.984 0l-4.512 2.578A1 1 0 0 1 5 20V5a2 2 0 0 1 2-2z" />
    </svg>
  )
}

function SortHeaderDropdown({
  colKey,
  colLabel,
  isNumeric,
  sortOption,
  onSortOptionChange,
}: {
  colKey: string
  colLabel: string
  isNumeric: boolean
  sortOption: SortOption
  onSortOptionChange: (v: SortOption) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const isActive = sortOption.key === colKey

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const ascLabel = isNumeric ? 'Terendah' : 'A-Z'
  const descLabel = isNumeric ? 'Tertinggi' : 'Z-A'

  const choose = (dir: 'asc' | 'desc') => {
    onSortOptionChange({ key: colKey, dir })
    setOpen(false)
  }

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setOpen((o) => !o)
        }}
        className="flex items-center gap-1"
      >
        {colLabel}
        <span className={`text-[10px] ${isActive ? 'text-blue-600' : 'text-gray-400'}`}>
          {isActive ? (sortOption.dir === 'asc' ? '▲' : '▼') : '⇅'}
        </span>
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-1 w-40 overflow-hidden rounded-lg border border-gray-200 bg-white py-1 normal-case shadow-lg">
          <button
            type="button"
            onClick={() => choose('asc')}
            className={`block w-full px-3 py-2 text-left text-sm font-normal tracking-normal ${
              isActive && sortOption.dir === 'asc' ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            {ascLabel}
          </button>
          <button
            type="button"
            onClick={() => choose('desc')}
            className={`block w-full px-3 py-2 text-left text-sm font-normal tracking-normal ${
              isActive && sortOption.dir === 'desc' ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            {descLabel}
          </button>
          {isActive && (
            <button
              type="button"
              onClick={() => {
                onSortOptionChange({ key: 'default', dir: 'asc' })
                setOpen(false)
              }}
              className="block w-full border-t border-gray-100 px-3 py-2 text-left text-xs font-normal tracking-normal text-gray-400 hover:bg-gray-50"
            >
              Reset ke Default
            </button>
          )}
        </div>
      )}
    </div>
  )
}

interface TableProps {
  data: WoKendari[]
  onRowClick: (item: WoKendari) => void
  pinnedIds: Set<number>
  sortOption: SortOption
  onSortOptionChange: (v: SortOption) => void
}

export default function WoTable({ data, onRowClick, pinnedIds, sortOption, onSortOptionChange }: TableProps) {
  const now = useNow()

  const sortWithPin = (a: WoKendari, b: WoKendari) => {
    const aPinned = pinnedIds.has(a.id) ? 1 : 0
    const bPinned = pinnedIds.has(b.id) ? 1 : 0
    if (aPinned !== bPinned) return bPinned - aPinned
    if (sortOption.key === 'default') return a.status_order - b.status_order
    return 0
  }

  const applySort = (rows: WoKendari[]) => {
    if (sortOption.key === 'default') return rows
    const sorted = [...rows].sort((a, b) => {
      if (sortOption.key === 'ttr') {
        const av = getTTRSeconds(a.reported_date, a.status, a.updated_at, a.booking_date)
        const bv = getTTRSeconds(b.reported_date, b.status, b.updated_at, b.booking_date)
        return av - bv
      }
      const av = String(a[sortOption.key as keyof WoKendari] ?? '').toLowerCase()
      const bv = String(b[sortOption.key as keyof WoKendari] ?? '').toLowerCase()
      return av.localeCompare(bv, 'id', { numeric: true })
    })
    return sortOption.dir === 'asc' ? sorted : sorted.reverse()
  }

  const active = applySort(data.filter((d) => ACTIVE_STATUSES.includes(d.status)).sort(sortWithPin))
  const inactive = applySort(data.filter((d) => !ACTIVE_STATUSES.includes(d.status)).sort(sortWithPin))

  if (data.length === 0) {
    return (
      <EmptyState
        title="Tidak ada tiket yang cocok"
        description="Coba ubah kata kunci pencarian atau filter status/rayon."
      />
    )
  }

  return (
    <div className="h-full overflow-auto rounded-xl border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full border-separate border-spacing-0 text-sm">
        <thead className="sticky top-0 z-30 border-b border-gray-200 bg-gray-50">
          <tr>
            {COLUMN_DEFS.map((col) => {
              const stickyOffset = getStickyOffset(col.key)
              const isSticky = stickyOffset !== null
              const isSortable = !NON_SORTABLE_KEYS.includes(col.key)
              return (
                <th
                  key={col.key}
                  style={
                    isSticky
                      ? { position: 'sticky', left: stickyOffset, zIndex: 40, width: STICKY_WIDTHS[col.key] }
                      : undefined
                  }
                  className={`whitespace-nowrap border-r border-gray-100 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wide text-gray-700 ${col.width ?? ''} ${
                    isSticky ? 'bg-gray-50' : ''
                  }`}
                >
                  {isSortable ? (
                    <SortHeaderDropdown
                      colKey={col.key}
                      colLabel={col.label}
                      isNumeric={col.key === 'ttr'}
                      sortOption={sortOption}
                      onSortOptionChange={onSortOptionChange}
                    />
                  ) : (
                    col.label
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {active.map((row) => (
            <RowItem key={row.id} row={row} onClick={() => onRowClick(row)} isPinned={pinnedIds.has(row.id)} now={now} />
          ))}

          {active.length > 0 && inactive.length > 0 && (
            <tr>
              <td colSpan={COLUMN_DEFS.length} className="bg-gray-50/60 py-2">
                <div className="mx-3 flex items-center gap-3">
                  <div className="h-px flex-1 bg-gray-200" />
                  <span className="whitespace-nowrap text-[10px] font-medium uppercase tracking-wider text-gray-400">
                    Selesai
                  </span>
                  <div className="h-px flex-1 bg-gray-200" />
                </div>
              </td>
            </tr>
          )}

          {inactive.map((row) => (
            <RowItem key={row.id} row={row} onClick={() => onRowClick(row)} isPinned={pinnedIds.has(row.id)} now={now} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RowItem({
  row,
  onClick,
  isPinned,
  now,
}: {
  row: WoKendari
  onClick: () => void
  isPinned: boolean
  now: number
}) {
  const rowStyle = row.bookmarked_by
    ? { backgroundColor: `${row.bookmark_color ?? '#ef4444'}1A` }
    : undefined

  const stickyBgForRow = row.bookmarked_by
    ? ''
    : isPinned
      ? 'bg-amber-50/60'
      : 'bg-white'

  return (
    <tr
      onClick={onClick}
      style={rowStyle}
      className={`cursor-pointer hover:bg-gray-50 ${!row.bookmarked_by && isPinned ? 'bg-amber-50/60' : ''}`}
    >
      {COLUMN_DEFS.map((col) => {
        const stickyOffset = getStickyOffset(col.key)
        const isSticky = stickyOffset !== null
        const stickyStyle = isSticky
          ? { position: 'sticky' as const, left: stickyOffset, zIndex: 20, width: STICKY_WIDTHS[col.key] }
          : undefined
        const stickyBg = isSticky ? stickyBgForRow : ''

        if (col.type === 'status') {
          return (
            <td key={col.key} style={stickyStyle} className={`border-r border-gray-100 px-3 py-2 ${stickyBg}`}>
              <span className={`inline-block whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusColor[row.status]}`}>
                {row.status}
              </span>
            </td>
          )
        }

        if (col.key === 'incident') {
          return (
            <td key={col.key} style={stickyStyle} className={`border-r border-gray-100 px-3 py-2 text-gray-800 ${stickyBg}`}>
              <span className="flex max-w-[220px] items-center gap-1.5 truncate">
                {isPinned && <PinIconSmall />}
                {row.bookmarked_by && <BookmarkIconSmall color={row.bookmark_color ?? '#ef4444'} />}
                <span className="truncate">{formatCell(row.incident, 'readonly')}</span>
              </span>
            </td>
          )
        }

        if (col.type === 'ttr') {
          void now
          return (
            <td
              key={col.key}
              style={stickyStyle}
              className={`border-r border-gray-100 px-3 py-2 font-mono text-xs font-semibold ${stickyBg} ${getTTRColorClass(row.reported_date, row.status, row.updated_at, row.booking_date)}`}
            >
              {formatTTR(row.reported_date, row.status, row.updated_at, row.booking_date)}
            </td>
          )
        }

        if (col.type === 'ttr_manja') {
          void now
          const { text, overdue } = formatManjaCountdown(row.booking_date)
          return (
            <td
              key={col.key}
              style={stickyStyle}
              className={`border-r border-gray-100 px-3 py-2 font-mono text-xs font-semibold ${stickyBg} ${overdue ? 'text-red-600' : 'text-blue-700'}`}
            >
              {text}
            </td>
          )
        }

        const value = row[col.key as keyof WoKendari]
        return (
          <td
            key={col.key}
            style={stickyStyle}
            className={`border-r border-gray-100 px-3 py-2 text-gray-800 ${stickyBg} ${col.editable ? 'cursor-text hover:bg-blue-50' : 'text-gray-600'}`}
          >
            <span className="block max-w-[220px] truncate">{formatCell(value, col.type)}</span>
          </td>
        )
      })}
    </tr>
  )
}