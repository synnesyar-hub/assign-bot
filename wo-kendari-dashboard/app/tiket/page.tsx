/* app/tiket/page.tsx */
'use client'

import { useMemo, useState } from 'react'
import WoTable from '@/components/WoTable'
import WoFilters from '@/components/WoFilters'
import IncidentDetailPanel from '@/components/IncidentDetailPanel'
import RecapAllButton from '@/components/RecapAllButton'
import { useAllTickets, WoTicketWithCity } from '@/lib/useAllTickets'
import { useCurrentUser } from '@/lib/useCurrentUser'
import { usePins } from '@/lib/usePins'
import { WoStatus, CITY_TABLE, SortOption } from '@/lib/types'

export default function TiketPage() {
  const { tickets, changeStatus } = useAllTickets()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<WoStatus | 'ALL'>('ALL')
  const [areaFilter, setAreaFilter] = useState<string[]>([]) // service_area, kosong = semua
  const [rayonFilter, setRayonFilter] = useState<string[]>([]) // rayon, kosong = semua
  const [sortHistory, setSortHistory] = useState<SortOption[]>([]) // kosong = default
  const [selected, setSelected] = useState<WoTicketWithCity | null>(null)
  const currentUser = useCurrentUser()
  const { pinnedIds, togglePin } = usePins(currentUser, 'all')

  const areaOptions = useMemo(
    () => Array.from(new Set(tickets.map((d) => d.service_area).filter(Boolean))) as string[],
    [tickets]
  )

  const rayonOptions = useMemo(
    () => Array.from(new Set(tickets.map((d) => d.rayon).filter(Boolean))) as string[],
    [tickets]
  )

  // Sort dilakukan sepenuhnya di WoTable (butuh pinnedIds + status_order)
  const filtered = useMemo(() => {
    return tickets.filter((row) => {
      const matchSearch =
        search.trim() === '' ||
        row.incident.toLowerCase().includes(search.toLowerCase()) ||
        (row.customer_name ?? '').toLowerCase().includes(search.toLowerCase())
      const matchStatus = statusFilter === 'ALL' || row.status === statusFilter
      const matchArea = areaFilter.length === 0 || (row.service_area && areaFilter.includes(row.service_area))
      const matchRayon = rayonFilter.length === 0 || (row.rayon && rayonFilter.includes(row.rayon))
      return matchSearch && matchStatus && matchArea && matchRayon
    })
  }, [tickets, search, statusFilter, areaFilter, rayonFilter])

  const selectedTicket = selected
    ? tickets.find((t) => t.id === selected.id && t._kota === selected._kota) ?? null
    : null

  return (
    <main className="flex h-full flex-col px-6 py-6 sm:px-8">
      <div className="mb-6 flex shrink-0 items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Semua Tiket</h1>
          <p className="mt-1 text-sm font-medium text-gray-600">
            Kelola dan pantau seluruh tiket WO — semua kota
          </p>
        </div>
        <RecapAllButton onDone={() => {}} />
      </div>

      <div className="shrink-0">
        <WoFilters
          search={search}
          onSearchChange={setSearch}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          areaOptions={areaOptions}
          areaFilter={areaFilter}
          onAreaFilterChange={setAreaFilter}
          rayonOptions={rayonOptions}
          rayonFilter={rayonFilter}
          onRayonFilterChange={setRayonFilter}
        />
      </div>

      <div className="min-h-0 min-w-0 flex-1">
        <WoTable
          data={filtered}
          onRowClick={(item) => setSelected(item as WoTicketWithCity)}
          pinnedIds={pinnedIds}
          sortHistory={sortHistory}
          onSortHistoryChange={setSortHistory}
        />
      </div>

      <IncidentDetailPanel
        item={selectedTicket}
        onClose={() => setSelected(null)}
        onStatusChange={(id, s) => selectedTicket && changeStatus(selectedTicket._kota, id, s)}
        table={selectedTicket ? CITY_TABLE[selectedTicket._kota] : ''}
        currentUser={currentUser}
        isPinned={selectedTicket ? pinnedIds.has(selectedTicket.id) : false}
        onTogglePin={() => selectedTicket && togglePin(selectedTicket.id)}
      />
    </main>
  )
}