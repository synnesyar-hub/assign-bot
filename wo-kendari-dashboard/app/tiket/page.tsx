/* assign-bot/wo-kendari-dashboard/app/tiket/page.tsx */

'use client'

import { useMemo, useState } from 'react'
import WoTable from '@/components/WoTable'
import WoFilters from '@/components/WoFilters'
import IncidentDetailPanel from '@/components/IncidentDetailPanel'
import RecapAllButton from '@/components/RecapAllButton'
import { useAllTickets, WoTicketWithCity } from '@/lib/useAllTickets'
import { useCurrentUser } from '@/lib/useCurrentUser'
import { usePins } from '@/lib/usePins'
import { WoStatus, CITY_TABLE, SortOption, SORT_OPTIONS } from '@/lib/types'
import { getTTRSeconds } from '@/lib/timeUtils'

export default function TiketPage() {
  const { tickets, changeStatus } = useAllTickets()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<WoStatus | 'ALL'>('ALL')
  const [areaFilter, setAreaFilter] = useState('ALL') // service_area, default SEMUA kota
  const [rayonFilter, setRayonFilter] = useState('ALL') // rayon
  const [sortOption, setSortOption] = useState<SortOption>(SORT_OPTIONS[0]) // default
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

  const filtered = useMemo(() => {
    const rows = tickets.filter((row) => {
      const matchSearch =
        search.trim() === '' ||
        row.incident.toLowerCase().includes(search.toLowerCase()) ||
        (row.customer_name ?? '').toLowerCase().includes(search.toLowerCase())
      const matchStatus = statusFilter === 'ALL' || row.status === statusFilter
      const matchArea = areaFilter === 'ALL' || row.service_area === areaFilter
      const matchRayon = rayonFilter === 'ALL' || row.rayon === rayonFilter
      return matchSearch && matchStatus && matchArea && matchRayon
    })

    if (sortOption.key === 'default') {
      return [...rows].sort((a, b) => a.status_order - b.status_order)
    }

    if (sortOption.key === 'ttr') {
      const sorted = [...rows].sort((a, b) => {
        const av = getTTRSeconds(a.reported_date, a.status, a.updated_at, a.booking_date)
        const bv = getTTRSeconds(b.reported_date, b.status, b.updated_at, b.booking_date)
        return av - bv
      })
      return sortOption.dir === 'asc' ? sorted : sorted.reverse()
    }

    const sorted = [...rows].sort((a, b) => {
      const av = String(a[sortOption.key as keyof WoTicketWithCity] ?? '').toLowerCase()
      const bv = String(b[sortOption.key as keyof WoTicketWithCity] ?? '').toLowerCase()
      return av.localeCompare(bv, 'id', { numeric: true })
    })
    return sortOption.dir === 'asc' ? sorted : sorted.reverse()
  }, [tickets, search, statusFilter, areaFilter, rayonFilter, sortOption])

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
          sortOption={sortOption}
          onSortOptionChange={setSortOption}
        />
      </div>

      <div className="min-h-0 min-w-0 flex-1">
        <WoTable
          data={filtered}
          onRowClick={(item) => setSelected(item as WoTicketWithCity)}
          pinnedIds={pinnedIds}
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