'use client'
import { useState } from 'react'
import { WoKendari } from '@/lib/types'
import Modal from '@/components/Modal'

const BAR_COLORS = [
  'from-blue-400 to-indigo-500',
  'from-purple-400 to-fuchsia-500',
  'from-orange-400 to-red-500',
  'from-emerald-400 to-teal-500',
  'from-amber-400 to-orange-500',
]

export default function RayonBreakdown({ data }: { data: WoKendari[] }) {
  const [open, setOpen] = useState(false)

  const counts = data.reduce<Record<string, number>>((acc, d) => {
    if (d.rayon) acc[d.rayon] = (acc[d.rayon] || 0) + 1
    return acc
  }, {})
  const max = Math.max(...Object.values(counts), 1)
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
  const topFive = sorted.slice(0, 5)

  return (
    <>
      <div className="rounded-2xl border border-gray-100 bg-gradient-to-br from-orange-50/40 to-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="text-sm font-bold text-gray-700">Insiden per Rayon</p>
          <button onClick={() => setOpen(true)} className="text-xs font-semibold text-blue-600 hover:text-blue-700">
            Lihat Semua →
          </button>
        </div>
        <div className="mt-5 space-y-5">
          {topFive.map(([rayon, count], i) => (
            <div key={rayon}>
              <div className="mb-1.5 flex justify-between text-sm">
                <span className="font-semibold text-gray-800">{rayon}</span>
                <span className="font-bold text-gray-700">{count} tiket</span>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${BAR_COLORS[i % BAR_COLORS.length]}`}
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <Modal title="Semua Rayon" isOpen={open} onClose={() => setOpen(false)}>
        <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
          {sorted.map(([rayon, count], i) => (
            <div key={rayon}>
              <div className="mb-1.5 flex justify-between text-sm">
                <span className="font-semibold text-gray-800">{rayon}</span>
                <span className="font-bold text-gray-700">{count} tiket</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${BAR_COLORS[i % BAR_COLORS.length]}`}
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </Modal>
    </>
  )
}