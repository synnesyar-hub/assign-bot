'use client'

import { useMemo, useState } from 'react'
import { notFound, useParams } from 'next/navigation'
import WoTable from '@/components/WoTable'
import WoFilters from '@/components/WoFilters'
import IncidentDetailPanel from '@/components/IncidentDetailPanel'
import RecapButton from '@/components/RecapButton'
import { useTickets } from '@/lib/useTickets'
import { useCurrentUser } from '@/lib/useCurrentUser'
import { usePins } from '@/lib/usePins'
import { WoKendari, WoStatus, CityKey, CITY_TABLE, CITY_LABEL, CITY_SYNC_FN, ALL_CITIES } from '@/lib/types'

export default function TiketPage() {
  const params = useParams()
  const kota = params.kota as string

  if (!ALL_CITIES.includes(kota as CityKey)) {
    notFound()
  }

  const cityKey = kota as CityKey
  const table = CITY_TABLE[cityKey]
  const label = CITY_LABEL[cityKey]

  const { tickets, changeStatus } = useTickets(table)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<WoStatus | 'ALL'>('ALL')
  const [rayonFilter, setRayonFilter] = useState('ALL')
  const [selected, setSelected] = useState<WoKendari | null>(null)

  const rayonOptions = useMemo(
    () => Array.from(new Set(tickets.map((d) => d.rayon).filter(Boolean))) as string[],
    [tickets]
  )

  const filtered = useMemo(() => {
    return tickets.filter((row) => {
      const matchSearch =
        search.trim() === '' ||
        row.incident.toLowerCase().includes(search.toLowerCase()) ||
        (row.customer_name ?? '').toLowerCase().includes(search.toLowerCase())
      const matchStatus = statusFilter === 'ALL' || row.status === statusFilter
      const matchRayon = rayonFilter === 'ALL' || row.rayon === rayonFilter
      return matchSearch && matchStatus && matchRayon
    })
  }, [tickets, search, statusFilter, rayonFilter])

  const selectedTicket = selected ? tickets.find((t) => t.id === selected.id) ?? null : null
  const currentUser = useCurrentUser()
  const { pinnedIds, togglePin } = usePins(currentUser, cityKey)

  return (
    <main className="min-h-screen px-6 py-6 sm:px-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Semua Tiket — {label}</h1>
          <p className="mt-1 text-sm font-medium text-gray-600">
            Kelola dan pantau seluruh tiket WO {label}
          </p>
        </div>
        <RecapButton syncFn={CITY_SYNC_FN[cityKey]} onDone={() => {}} />
      </div>

      <WoFilters
        search={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        rayonOptions={rayonOptions}
        rayonFilter={rayonFilter}
        onRayonFilterChange={setRayonFilter}
      />

      <WoTable data={filtered} onRowClick={setSelected} pinnedIds={pinnedIds} />

      <IncidentDetailPanel
        item={selectedTicket}
        onClose={() => setSelected(null)}
        onStatusChange={changeStatus}
        table={table}
        currentUser={currentUser}
        isPinned={selectedTicket ? pinnedIds.has(selectedTicket.id) : false}
        onTogglePin={() => selectedTicket && togglePin(selectedTicket.id)}
      />
    </main>
  )
}