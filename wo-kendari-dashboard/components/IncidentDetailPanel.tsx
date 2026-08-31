'use client'
import { useState, useEffect, useRef } from 'react'
import { WoKendari, WoStatus, ALL_STATUSES } from '@/lib/types'
import { statusColor } from '@/lib/statusStyle'
import { getAgeInHours, formatAge, getSlaLevel, formatTTR, formatManjaCountdown, getTTRColorClass } from '@/lib/timeUtils'
import { usePresence } from '@/context/PresenceContext'
import { TicketEditorBadge } from '@/components/TicketEditorBadge'
import { useDebouncedSave } from '@/lib/useDebouncedSave'
import { toggleBookmark } from '@/lib/useBookmark'
import BookmarkGuardDialog from '@/components/BookmarkGuardDialog'
import { useNow } from '@/lib/useNow'

interface Props {
  item: WoKendari | null
  onClose: () => void
  onStatusChange: (id: number, newStatus: WoStatus) => void
  table: string
  currentUser: string
  isPinned: boolean
  onTogglePin: () => void
}

const slaStyle = {
  ok: 'bg-gray-100 text-gray-600',
  warning: 'bg-amber-100 text-amber-700',
  breach: 'bg-red-100 text-red-700',
}

function PinIcon({ filled }: { filled: boolean }) {
  return filled ? (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="icon icon-tabler icons-tabler-filled icon-tabler-pin">
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M15.113 3.21l.094 .083l5.5 5.5a1 1 0 0 1 -1.175 1.59l-3.172 3.171l-1.424 3.797a1 1 0 0 1 -.158 .277l-.07 .08l-1.5 1.5a1 1 0 0 1 -1.32 .082l-.095 -.083l-2.793 -2.792l-3.793 3.792a1 1 0 0 1 -1.497 -1.32l.083 -.094l3.792 -3.793l-2.792 -2.793a1 1 0 0 1 -.083 -1.32l.083 -.094l1.5 -1.5a1 1 0 0 1 .258 -.187l.098 -.042l3.796 -1.425l3.171 -3.17a1 1 0 0 1 1.497 -1.26z" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon icon-tabler icons-tabler-outline icon-tabler-pin">
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M15 4.5l-4 4l-4 1.5l-1.5 1.5l7 7l1.5 -1.5l1.5 -4l4 -4" />
      <path d="M9 15l-4.5 4.5" />
      <path d="M14.5 4l5.5 5.5" />
    </svg>
  )
}

function BookmarkIcon({ filled, color }: { filled: boolean; color?: string }) {
  return filled ? (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill={color ?? 'currentColor'} stroke="none">
      <path d="M17 3a2 2 0 0 1 2 2v15a1 1 0 0 1-1.496.868l-4.512-2.578a2 2 0 0 0-1.984 0l-4.512 2.578A1 1 0 0 1 5 20V5a2 2 0 0 1 2-2z" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 3a2 2 0 0 1 2 2v15a1 1 0 0 1-1.496.868l-4.512-2.578a2 2 0 0 0-1.984 0l-4.512 2.578A1 1 0 0 1 5 20V5a2 2 0 0 1 2-2z" />
    </svg>
  )
}

function PencilIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="inline-block h-3.5 w-3.5 shrink-0">
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
    </svg>
  )
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-[11px] font-bold uppercase tracking-wide text-gray-600">{label}</p>
      <p className="mt-0.5 text-sm font-medium text-gray-900">{value || '-'}</p>
    </div>
  )
}

function EditableField({
  label,
  value,
  column,
  ticketId,
  table,
  currentUser,
  onSaved,
  locked,
  onLockedFocusAttempt,
}: {
  label: string
  value: string | null | undefined
  column: string
  ticketId: number
  table: string
  currentUser: string
  onSaved: (user: string, at: string) => void
  locked: boolean
  onLockedFocusAttempt: () => void
}) {
  const { setEditing } = usePresence()
  const save = useDebouncedSave(table, () => onSaved(currentUser, new Date().toISOString()))
  const [localValue, setLocalValue] = useState(value ?? '')
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const autoResize = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }

  useEffect(() => {
    autoResize()
  }, [])

  const startHeartbeat = () => {
    setEditing(String(ticketId), column)
    heartbeatRef.current = setInterval(() => {
      setEditing(String(ticketId), column)
    }, 3000)
  }

  const stopHeartbeat = () => {
    if (heartbeatRef.current) clearInterval(heartbeatRef.current)
    heartbeatRef.current = null
    setEditing(null, null)
  }

  useEffect(() => {
    return () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current)
    }
  }, [])

  return (
    <div>
      <p className="text-[11px] font-bold uppercase tracking-wide text-gray-600">{label}</p>
      <textarea
        ref={textareaRef}
        value={localValue}
        rows={1}
        onFocus={(e) => {
          if (locked) {
            e.target.blur()
            onLockedFocusAttempt()
            return
          }
          startHeartbeat()
        }}
        onChange={(e) => {
          setLocalValue(e.target.value)
          autoResize()
          save(ticketId, column, e.target.value, currentUser)
        }}
        onBlur={stopHeartbeat}
        className="mt-0.5 w-full resize-none overflow-hidden rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm font-medium text-gray-900 shadow-sm hover:border-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
      />
    </div>
  )
}

export default function IncidentDetailPanel({
  item,
  onClose,
  onStatusChange,
  table,
  currentUser,
  isPinned,
  onTogglePin,
}: Props) {
  const [lastUpdated, setLastUpdated] = useState<{ user: string; at: string } | null>(null)
  const [showGuard, setShowGuard] = useState(false)
  const [unlockedOnce, setUnlockedOnce] = useState(false)
  const now = useNow()

  useEffect(() => {
    if (item) setLastUpdated(item.updated_by ? { user: item.updated_by, at: item.updated_at } : null)
    setUnlockedOnce(false)
  }, [item?.id])

  if (!item) return null
  const age = getAgeInHours(item.reported_date)
  const level = getSlaLevel(age)
  void now
  const ttrText = formatTTR(item.reported_date, item.status, item.updated_at, item.booking_date)
  const ttrColorClass = getTTRColorClass(item.reported_date, item.status, item.updated_at, item.booking_date)
  const manja = formatManjaCountdown(item.booking_date)

  const handleSaved = (user: string, at: string) => setLastUpdated({ user, at })

  const isBookmarkedByOther = !!item.bookmarked_by && item.bookmarked_by !== currentUser
  const isBookmarkedByMe = item.bookmarked_by === currentUser
  const fieldsLocked = isBookmarkedByOther && !unlockedOnce

  const handleTogglePinnedBookmark = async () => {
    const { error } = await toggleBookmark(table, item, currentUser)
    if (error) alert(error)
  }

  return (
    <>
      <div className="fixed inset-0 z-20 bg-black/20" onClick={onClose} />
      <div className="fixed right-0 top-0 z-30 h-full w-full max-w-md overflow-y-auto bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <p className="text-xs text-gray-400">Detail Tiket</p>
            <h2 className="text-lg font-bold text-gray-900">{item.incident}</h2>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={onTogglePin}
              className={`rounded-full p-2 ${isPinned ? 'text-amber-500' : 'text-gray-300 hover:text-gray-400'}`}
              title={isPinned ? 'Lepas penanda' : 'Tandai tiket ini'}
            >
              <PinIcon filled={isPinned} />
            </button>
            <button
              onClick={handleTogglePinnedBookmark}
              disabled={isBookmarkedByOther}
              className={`rounded-full p-2 disabled:cursor-not-allowed disabled:opacity-40 ${!isBookmarkedByMe ? 'text-gray-300 hover:text-gray-400' : ''}`}
              title={isBookmarkedByMe ? 'Lepas bookmark' : 'Bookmark tiket ini'}
            >
              <BookmarkIcon filled={isBookmarkedByMe} color={isBookmarkedByMe ? (item.bookmark_color ?? '#ef4444') : undefined} />
            </button>
            <button onClick={onClose} className="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700">
              ✕
            </button>
          </div>
        </div>

        <div className="space-y-6 px-6 py-5">
          <div className="flex items-start justify-between">
            <TicketEditorBadge ticketId={String(item.id)} />
            {item.bookmarked_by && (
              <span className="flex items-center gap-1 text-xs font-medium" style={{ color: item.bookmark_color ?? '#ef4444' }}>
                <BookmarkIcon filled color={item.bookmark_color ?? '#ef4444'} />
                {item.bookmarked_by}
              </span>
            )}
          </div>

          {lastUpdated && (
            <div className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2">
              <p className="text-xs font-medium text-blue-800">
                Terakhir diupdate oleh <strong>{lastUpdated.user}</strong>
              </p>
              <p className="text-[11px] text-blue-600">
                {new Date(lastUpdated.at).toLocaleString('id-ID')}
              </p>
            </div>
          )}

          <div>
            <p className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-gray-600">
              Ubah Status
            </p>
            <select
              value={item.status}
              onChange={(e) => onStatusChange(item.id, e.target.value as WoStatus)}
              className={`w-full rounded-lg border px-3 py-2 text-sm font-medium shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-300 ${statusColor[item.status]}`}
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <span className={`mt-2 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${slaStyle[level]}`}>
              {formatAge(age)} sejak lapor
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Nama Pelanggan" value={item.customer_name} />
            <Field label="No. HP" value={item.contact_phone} />
            <Field label="Tipe Pelanggan" value={item.customer_type} />
            <Field label="No. Layanan" value={item.service_no} />
            <Field label="Rayon" value={item.rayon} />
            <Field label="STO / ODC" value={`${item.sto ?? '-'} / ${item.odc ?? '-'}`} />
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wide text-gray-600">TTR</p>
              <p className={`mt-0.5 font-mono text-sm font-semibold ${ttrColorClass}`}>{ttrText}</p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wide text-gray-600">TTR Manja</p>
              <p className={`mt-0.5 font-mono text-sm font-semibold ${manja.overdue ? 'text-red-600' : 'text-blue-700'}`}>
                {manja.text}
              </p>
            </div>
          </div>

          <div className="border-t border-gray-100 pt-4">
            <p className="mb-3 text-xs font-bold uppercase tracking-wide text-gray-600">
              Penanganan
            </p>
            <div className="space-y-4">
              <EditableField label="Teknisi" value={item.teknisi} column="teknisi" ticketId={item.id} table={table} currentUser={currentUser} onSaved={handleSaved} locked={fieldsLocked} onLockedFocusAttempt={() => setShowGuard(true)} />
              <EditableField label="Kendala" value={item.kendala} column="kendala" ticketId={item.id} table={table} currentUser={currentUser} onSaved={handleSaved} locked={fieldsLocked} onLockedFocusAttempt={() => setShowGuard(true)} />
              <EditableField label="Perbaikan" value={item.perbaikan} column="perbaikan" ticketId={item.id} table={table} currentUser={currentUser} onSaved={handleSaved} locked={fieldsLocked} onLockedFocusAttempt={() => setShowGuard(true)} />
              <EditableField label="Kategori TTR" value={item.kategori_ttr} column="kategori_ttr" ticketId={item.id} table={table} currentUser={currentUser} onSaved={handleSaved} locked={fieldsLocked} onLockedFocusAttempt={() => setShowGuard(true)} />
              <EditableField label="Status TTR" value={item.status_ttr} column="status_ttr" ticketId={item.id} table={table} currentUser={currentUser} onSaved={handleSaved} locked={fieldsLocked} onLockedFocusAttempt={() => setShowGuard(true)} />
              <EditableField label="Job" value={item.job} column="job" ticketId={item.id} table={table} currentUser={currentUser} onSaved={handleSaved} locked={fieldsLocked} onLockedFocusAttempt={() => setShowGuard(true)} />
            </div>
          </div>
        </div>
      </div>

      {showGuard && item.bookmarked_by && (
        <BookmarkGuardDialog
          bookmarkedBy={item.bookmarked_by}
          onCancel={() => setShowGuard(false)}
          onConfirm={() => {
            setUnlockedOnce(true)
            setShowGuard(false)
          }}
        />
      )}
    </>
  )
}