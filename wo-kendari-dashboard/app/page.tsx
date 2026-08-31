'use client'

import HeroMetric from '@/components/HeroMetric'
import IncidentTrend from '@/components/IncidentTrend'
import RayonBreakdown from '@/components/RayonBreakdown'
import StatusSummary from '@/components/StatusSummary'
import StatusDonut from '@/components/StatusDonut'
import WeekComparison from '@/components/WeekComparison'
import { useTickets } from '@/lib/useTickets'
import { countThisWeek, countLastWeek } from '@/lib/timeUtils'
import { useMemo } from 'react'
import { WoKendari } from '@/lib/types'

export default function Home() {
  const kendari = useTickets('wo_kendari')
  const kolaka = useTickets('wo_kolaka')
  const baubau = useTickets('wo_baubau')

  const isLoading = kendari.isLoading || kolaka.isLoading || baubau.isLoading

  const tickets: WoKendari[] = useMemo(
    () => [...kendari.tickets, ...kolaka.tickets, ...baubau.tickets],
    [kendari.tickets, kolaka.tickets, baubau.tickets]
  )

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-gray-500">Memuat data...</p>
      </main>
    )
  }

  const thisWeek = countThisWeek(tickets)
  const lastWeek = countLastWeek(tickets)

  return (
    <main className="min-h-screen bg-slate-50/50 px-6 py-8 sm:px-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Board Insiden</h1>
        <p className="mt-1 text-sm font-medium text-gray-600">
          Ringkasan statistik penanganan WO — Kendari, Kolaka, Baubau
        </p>
      </div>

      <div className="mb-8">
        <HeroMetric data={tickets} />
      </div>

      <div className="mb-8">
        <StatusSummary data={tickets} />
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-6">
        <div className="lg:col-span-4">
          <IncidentTrend data={tickets} />
        </div>
        <div className="lg:col-span-2">
          <WeekComparison thisWeek={thisWeek} lastWeek={lastWeek} />
        </div>

        <div className="lg:col-span-2">
          <StatusDonut data={tickets} />
        </div>
        <div className="lg:col-span-4">
          <RayonBreakdown data={tickets} />
        </div>
      </div>
    </main>
  )
}