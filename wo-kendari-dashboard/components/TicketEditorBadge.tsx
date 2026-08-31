'use client'

import { usePresence } from '@/context/PresenceContext'

function PencilIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="inline-block h-3.5 w-3.5 shrink-0">
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
    </svg>
  )
}

export function TicketEditorBadge({ ticketId }: { ticketId: string }) {
  const { presenceState } = usePresence()

  const editors = Object.values(presenceState)
    .flat()
    .filter((p) => p.ticketId === ticketId)

  if (editors.length === 0) return null

  return (
    <div className="flex flex-col gap-1 text-xs text-amber-600">
      {editors.map((p) => (
        <span key={`${p.user}-${p.column}`} className="flex items-center gap-1">
          <PencilIcon />
          <strong>{p.user}</strong> sedang mengisi kolom &quot;{p.column}&quot;
        </span>
      ))}
    </div>
  )
}