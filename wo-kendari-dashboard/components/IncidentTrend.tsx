'use client'
import { useMemo, useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import Modal from '@/components/Modal'
import { WoKendari } from '@/lib/types'

const DAY_LABELS = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab']

interface Props {
  data: WoKendari[]
}

export default function IncidentTrend({ data: tickets }: Props) {
  const [open, setOpen] = useState(false)

  const data = useMemo(() => {
    // bangun 7 hari terakhir (termasuk hari ini), urut dari yang paling lama
    const days: { key: string; day: string; total: number }[] = []
    for (let i = 6; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      const key = d.toISOString().slice(0, 10) // YYYY-MM-DD
      days.push({ key, day: DAY_LABELS[d.getDay()], total: 0 })
    }

    const dayMap = new Map(days.map((d) => [d.key, d]))

    tickets.forEach((t) => {
      if (!t.reported_date) return
      const key = new Date(t.reported_date).toISOString().slice(0, 10)
      const bucket = dayMap.get(key)
      if (bucket) bucket.total += 1
    })

    return days
  }, [tickets])

  const totalAll = data.reduce((a, b) => a + b.total, 0)
  const avg = data.length > 0 ? Math.round((totalAll / data.length) * 10) / 10 : 0
  const peak = data.length > 0 ? data.reduce((a, b) => (b.total > a.total ? b : a)) : { day: '-', total: 0 }

  return (
    <>
      <div className="rounded-2xl border border-gray-100 bg-gradient-to-br from-blue-50/40 to-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="text-sm font-bold text-gray-700">Insiden Masuk (7 Hari)</p>
          <button onClick={() => setOpen(true)} className="text-xs font-semibold text-blue-600 hover:text-blue-700">
            Lihat Laporan →
          </button>
        </div>

        <div className="mt-4 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="#e2e8f0" strokeDasharray="4 4" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} fontSize={12} fontWeight={600} stroke="#64748b" />
              <YAxis axisLine={false} tickLine={false} fontSize={11} stroke="#94a3b8" width={24} allowDecimals={false} />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null
                  return (
                    <div className="rounded-xl bg-gray-900 px-3 py-2 text-white shadow-lg">
                      <p className="text-xs text-gray-300">{label}</p>
                      <p className="text-sm font-bold">{payload[0].value} insiden</p>
                    </div>
                  )
                }}
              />
              <Area
                type="monotone"
                dataKey="total"
                stroke="#2563eb"
                strokeWidth={2.5}
                fill="url(#trendFill)"
                dot={{ r: 4, fill: '#2563eb', strokeWidth: 2, stroke: '#fff' }}
                activeDot={{ r: 6 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 flex items-center gap-4 border-t border-gray-100 pt-3 text-xs">
          <div>
            <span className="font-medium text-gray-500">Total: </span>
            <span className="font-bold text-gray-900">{totalAll}</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Rata-rata: </span>
            <span className="font-bold text-gray-900">{avg}/hari</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Puncak: </span>
            <span className="font-bold text-gray-900">{peak.day} ({peak.total})</span>
          </div>
        </div>
      </div>

      <Modal title="Laporan Insiden 7 Hari" isOpen={open} onClose={() => setOpen(false)}>
        <div className="space-y-3">
          {data.map((d) => (
            <div key={d.key} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <span className="text-sm font-semibold text-gray-700">{d.day}</span>
              <span className="text-sm font-bold text-gray-900">{d.total} insiden</span>
            </div>
          ))}
          <div className="flex items-center justify-between rounded-lg bg-blue-50 px-3 py-2">
            <span className="text-sm font-bold text-blue-700">Total 7 Hari</span>
            <span className="text-sm font-bold text-blue-700">{totalAll} insiden</span>
          </div>
        </div>
      </Modal>
    </>
  )
}