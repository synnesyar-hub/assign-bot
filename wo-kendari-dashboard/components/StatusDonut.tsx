/* components/StatusDonut.tsx */
'use client'

import { WoKendari, WoStatus } from '@/lib/types'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const ALL_STATUSES: WoStatus[] = [
  'OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING', 'CLOSE CROSSCHECK', 'CLOSE',
]

const COLOR: Record<WoStatus, string> = {
  OPEN: '#ef4444',
  MONITORING: '#f59e0b',
  GAMAS: '#fb923c',
  KENDALA: '#a855f7',
  PENDING: '#3b82f6',
  'CLOSE CROSSCHECK': '#94a3b8',
  CLOSE: '#10b981',
}

export default function StatusDonut({ data }: { data: WoKendari[] }) {
  const chartData = ALL_STATUSES.map((status) => ({
    name: status,
    value: data.filter((d) => d.status === status).length,
  })).filter((d) => d.value > 0)

  return (
    <div className="rounded-2xl border border-gray-100 bg-gradient-to-br from-purple-50/40 to-white p-6 shadow-sm">
      <p className="text-sm font-bold text-gray-700">Distribusi Status</p>
        <div className="relative mt-2 h-64">
        <ResponsiveContainer width="100%" height="100%">
            <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={65}
              outerRadius={95}
              paddingAngle={3}
              cornerRadius={6}
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={COLOR[entry.name as WoStatus]} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const item = payload[0]
                const chartTotal = chartData.reduce((a, b) => a + b.value, 0)
                const pct = chartTotal === 0 ? 0 : Math.round((Number(item.value) / chartTotal) * 100)
                return (
                  <div className="rounded-xl bg-gray-900 px-3 py-2 text-white shadow-lg">
                    <p className="text-xs text-gray-300">{item.name}</p>
                    <p className="text-sm font-bold">{item.value} tiket ({pct}%)</p>
                  </div>
                )
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-gray-900">
            {chartData.reduce((a, b) => a + b.value, 0)}
            </span>
            <span className="text-xs font-medium text-gray-500">Total Tiket</span>
        </div>
        </div>
      <div className="mt-3 space-y-2">
        {[...chartData]
          .sort((a, b) => b.value - a.value)
          .map((entry) => {
            const total = chartData.reduce((a, b) => a + b.value, 0)
            const pct = total === 0 ? 0 : Math.round((entry.value / total) * 100)
            return (
              <div key={entry.name} className="flex items-center gap-2 text-xs">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: COLOR[entry.name as WoStatus] }}
                />
                <span className="font-semibold text-gray-700">{entry.name}</span>
                <div className="ml-auto flex items-center gap-2">
                  <span className="font-bold text-gray-900">{entry.value}</span>
                  <span className="w-9 text-right text-gray-400">{pct}%</span>
                </div>
              </div>
            )
          })}
      </div>
    </div>
  )
}