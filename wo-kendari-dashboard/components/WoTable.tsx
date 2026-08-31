'use client'

import EmptyState from '@/components/EmptyState'
import { WoKendari, COLUMN_DEFS, ACTIVE_STATUSES } from '@/lib/types'
import { statusColor } from '@/lib/statusStyle'
import { formatTTR, formatManjaCountdown, getTTRColorClass } from '@/lib/timeUtils'
import { useNow } from '@/lib/useNow'

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

interface TableProps {
  data: WoKendari[]
  onRowClick: (item: WoKendari) => void
  pinnedIds: Set<number>
}

export default function WoTable({ data, onRowClick, pinnedIds }: TableProps) {
  const now = useNow() // ikut serta supaya kolom TTR/TTR Manja re-render tiap detik

  const sortWithPin = (a: WoKendari, b: WoKendari) => {
    const aPinned = pinnedIds.has(a.id) ? 1 : 0
    const bPinned = pinnedIds.has(b.id) ? 1 : 0
    if (aPinned !== bPinned) return bPinned - aPinned
    return a.status_order - b.status_order
  }

  const active = data
    .filter((d) => ACTIVE_STATUSES.includes(d.status))
    .sort(sortWithPin)

  const inactive = data
    .filter((d) => !ACTIVE_STATUSES.includes(d.status))
    .sort(sortWithPin)

  if (data.length === 0) {
    return (
      <EmptyState
        title="Tidak ada tiket yang cocok"
        description="Coba ubah kata kunci pencarian atau filter status/rayon."
      />
    )
  }

  return (
    <div className="h-[calc(100vh-220px)] overflow-auto rounded-xl border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full border-collapse text-sm">
        <thead className="sticky top-0 z-10 border-b border-gray-200 bg-gray-50">
          <tr>
            {COLUMN_DEFS.map((col) => (
              <th
                key={col.key}
                className={`whitespace-nowrap border-r border-gray-100 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wide text-gray-700 ${col.width ?? ''}`}
              >
                {col.label}
              </th>
            ))}
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

  return (
    <tr
      onClick={onClick}
      style={rowStyle}
      className={`cursor-pointer hover:bg-gray-50 ${!row.bookmarked_by && isPinned ? 'bg-amber-50/60' : ''}`}
    >
      {COLUMN_DEFS.map((col) => {
        if (col.type === 'status') {
          return (
            <td key={col.key} className="border-r border-gray-100 px-3 py-2">
              <span className={`inline-block whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusColor[row.status]}`}>
                {row.status}
              </span>
            </td>
          )
        }

        if (col.key === 'incident') {
          return (
            <td key={col.key} className="border-r border-gray-100 px-3 py-2 text-gray-800">
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
              className={`border-r border-gray-100 px-3 py-2 font-mono text-xs font-semibold ${getTTRColorClass(row.reported_date, row.status, row.updated_at, row.booking_date)}`}
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
              className={`border-r border-gray-100 px-3 py-2 font-mono text-xs font-semibold ${overdue ? 'text-red-600' : 'text-blue-700'}`}
            >
              {text}
            </td>
          )
        }

        const value = row[col.key as keyof WoKendari]
        return (
          <td
            key={col.key}
            className={`border-r border-gray-100 px-3 py-2 text-gray-800 ${col.editable ? 'cursor-text hover:bg-blue-50' : 'text-gray-600'}`}
          >
            <span className="block max-w-[220px] truncate">{formatCell(value, col.type)}</span>
          </td>
        )
      })}
    </tr>
  )
}