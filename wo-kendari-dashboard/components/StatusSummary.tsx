'use client'

import { WoKendari, WoStatus } from '@/lib/types'
import { getDailyTrendByStatus } from '@/lib/timeUtils'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

const ALL_STATUSES: WoStatus[] = [
  'OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING', 'CLOSE CROSSCHECK', 'CLOSE',
]

const cardStyle: Record<WoStatus, { bg: string; icon: string; line: string; text: string }> = {
  OPEN: { bg: 'from-red-50 to-orange-50', icon: 'bg-red-500', line: '#ef4444', text: 'text-red-700' },
  MONITORING: { bg: 'from-amber-50 to-yellow-50', icon: 'bg-amber-500', line: '#f59e0b', text: 'text-amber-700' },
  GAMAS: { bg: 'from-orange-50 to-amber-50', icon: 'bg-orange-500', line: '#fb923c', text: 'text-orange-700' },
  KENDALA: { bg: 'from-purple-50 to-fuchsia-50', icon: 'bg-purple-500', line: '#a855f7', text: 'text-purple-700' },
  PENDING: { bg: 'from-blue-50 to-sky-50', icon: 'bg-blue-500', line: '#3b82f6', text: 'text-blue-700' },
  'CLOSE CROSSCHECK': { bg: 'from-slate-50 to-gray-50', icon: 'bg-slate-400', line: '#94a3b8', text: 'text-slate-600' },
  CLOSE: { bg: 'from-emerald-50 to-teal-50', icon: 'bg-emerald-500', line: '#10b981', text: 'text-emerald-700' },
}

export default function StatusSummary({ data }: { data: WoKendari[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-7">
      {ALL_STATUSES.map((status) => {
        const count = data.filter((d) => d.status === status).length
        const style = cardStyle[status]
        const trend = getDailyTrendByStatus(data, status)

        return (
          <div
            key={status}
            className={`rounded-2xl bg-gradient-to-br p-4 shadow-sm ${style.bg}`}
          >
            <div className="flex items-center justify-between">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full ${style.icon}`}>
                <span className="h-2 w-2 rounded-full bg-white" />
              </div>
            </div>

            <p className={`mt-3 text-[11px] font-bold uppercase tracking-wide ${style.text}`}>
              {status}
            </p>
            <p className="mt-0.5 text-2xl font-bold text-gray-900">{count}</p>

            <div className="mt-2 h-8">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend}>
                  <Line
                    type="monotone"
                    dataKey="v"
                    stroke={style.line}
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )
      })}
    </div>
  )
}