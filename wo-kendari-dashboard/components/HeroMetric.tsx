'use client'
import { WoKendari } from '@/lib/types'
import { getAgeInHours, getSlaLevel } from '@/lib/timeUtils'

export default function HeroMetric({ data }: { data: WoKendari[] }) {
  const breached = data.filter(
    (d) => d.status !== 'CLOSE' && d.status !== 'CLOSE CROSSCHECK' &&
      getSlaLevel(getAgeInHours(d.reported_date)) === 'breach'
  ).length
  const total = data.length
  const safe = breached === 0

  return (
    <div className={`rounded-2xl p-6 shadow-sm ${
        safe
          ? 'bg-gradient-to-br from-emerald-500 to-teal-600'
          : 'bg-gradient-to-br from-red-500 to-orange-600'
      } text-white`}>
      <p className="text-sm font-semibold text-white/90">
        {safe ? 'Semua insiden dalam SLA' : 'Tiket melewati SLA (>24 jam)'}
      </p>
      <div className="mt-1 flex items-end gap-3">
        <span className="text-5xl font-bold leading-none">{breached}</span>
        <span className="pb-1 text-sm text-white/80">dari {total} tiket aktif</span>
      </div>
    </div>
  )
}