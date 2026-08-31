'use client'
import { WoKendari } from '@/lib/types'

interface Props {
  thisWeek: number
  lastWeek: number
}

export default function WeekComparison({ thisWeek, lastWeek }: Props) {
  const diff = thisWeek - lastWeek
  const pct = lastWeek === 0 ? 0 : Math.round((diff / lastWeek) * 100)
  const isUp = diff > 0
  const isFlat = diff === 0

  return (
    <div className="rounded-2xl border border-gray-100 bg-gradient-to-br from-emerald-50/40 to-white p-6 shadow-sm">
      <p className="text-sm font-bold text-gray-700">Minggu Ini vs Minggu Lalu</p>
      <div className="mt-4 flex items-end gap-4">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-gray-500">Minggu Ini</p>
          <p className="text-3xl font-bold text-gray-900">{thisWeek}</p>
        </div>
        <div className="pb-1.5 text-gray-300">/</div>
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-gray-500">Minggu Lalu</p>
          <p className="text-xl font-semibold text-gray-400">{lastWeek}</p>
        </div>
      </div>

      <div
        className={`mt-4 inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
          isFlat
            ? 'bg-gray-100 text-gray-500'
            : isUp
            ? 'bg-red-50 text-red-600'
            : 'bg-emerald-50 text-emerald-600'
        }`}
      >
        <span>{isFlat ? '—' : isUp ? '▲' : '▼'}</span>
        <span>{isFlat ? 'Tidak berubah' : `${Math.abs(pct)}% dari minggu lalu`}</span>
      </div>
    </div>
  )
}