'use client'

import { useState } from 'react'
import {
  DndContext,
  DragEndEvent,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  PointerSensor,
} from '@dnd-kit/core'
import { WoKendari, WoStatus } from '@/lib/types'
import { statusColor } from '@/lib/statusStyle'
import { getAgeInHours, formatAge, getSlaLevel } from '@/lib/timeUtils'

const COLUMNS: WoStatus[] = ['OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING']

const slaStyle = {
  ok: 'bg-gray-100 text-gray-500',
  warning: 'bg-amber-100 text-amber-700',
  breach: 'bg-red-100 text-red-700',
}

interface Props {
  data: WoKendari[]
  onSelect: (item: WoKendari) => void
  onStatusChange: (id: number, newStatus: WoStatus) => void
}

function Card({ item, onSelect }: { item: WoKendari; onSelect: (item: WoKendari) => void }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: item.id,
  })
  const age = getAgeInHours(item.reported_date)
  const level = getSlaLevel(age)

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      onClick={() => onSelect(item)}
      style={{
        transform: transform ? `translate(${transform.x}px, ${transform.y}px)` : undefined,
        opacity: isDragging ? 0.5 : 1,
      }}
      className="cursor-grab rounded-xl border border-gray-100 bg-white p-3 shadow-sm transition-shadow hover:shadow-md active:cursor-grabbing"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-gray-900">{item.incident}</p>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${slaStyle[level]}`}>
          {formatAge(age)}
        </span>
      </div>
      <p className="mt-0.5 truncate text-xs text-gray-500">{item.customer_name}</p>
      <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusColor[item.status]}`}>
        {item.rayon}
      </span>
    </div>
  )
}

function Column({
  status, items, onSelect,
}: { status: WoStatus; items: WoKendari[]; onSelect: (item: WoKendari) => void }) {
  const { setNodeRef, isOver } = useDroppable({ id: status })

  return (
    <div
      ref={setNodeRef}
      className={`flex max-h-[520px] flex-col rounded-2xl p-3 transition-colors ${isOver ? 'bg-blue-50' : 'bg-white/60'}`}
    >
      <div className="mb-3 flex shrink-0 items-center justify-between px-1">
        <span className="text-xs font-bold uppercase tracking-wide text-gray-700">{status}</span>
        <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-600">
          {items.length}
        </span>
      </div>
      <div className="space-y-2 overflow-y-auto pr-1">
        {items.map((item) => (
          <Card key={item.id} item={item} onSelect={onSelect} />
        ))}
        {items.length === 0 && (
          <p className="rounded-lg border border-dashed border-gray-200 px-2 py-4 text-center text-xs text-gray-400">
            Tidak ada tiket
          </p>
        )}
      </div>
    </div>
  )
}

export default function IncidentBoard({ data, onSelect, onStatusChange }: Props) {
  const [boardSearch, setBoardSearch] = useState('')

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    })
  )

  const visible = data.filter(
    (d) =>
      boardSearch.trim() === '' ||
      d.incident.toLowerCase().includes(boardSearch.toLowerCase()) ||
      (d.customer_name ?? '').toLowerCase().includes(boardSearch.toLowerCase())
  )

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over) return
    const newStatus = over.id as WoStatus
    onStatusChange(Number(active.id), newStatus)
  }

  return (
    <div>
      <div className="mb-3">
        <input
          type="text"
          placeholder="Cari di board (incident / nama pelanggan)..."
          value={boardSearch}
          onChange={(e) => setBoardSearch(e.target.value)}
          className="w-full max-w-xs rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm placeholder:text-gray-400 focus:border-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-300"
        />
      </div>

      <DndContext id="incident-board-dnd" sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="-mx-6 overflow-x-auto px-6 pb-2 sm:mx-0 sm:overflow-visible sm:px-0">
          <div className="grid w-max grid-flow-col auto-cols-[260px] gap-3 sm:w-full sm:grid-flow-row sm:auto-cols-auto sm:grid-cols-5">
            {COLUMNS.map((status) => (
              <Column
                key={status}
                status={status}
                items={visible.filter((d) => d.status === status)}
                onSelect={onSelect}
              />
            ))}
          </div>
        </div>
      </DndContext>
    </div>
  )
}