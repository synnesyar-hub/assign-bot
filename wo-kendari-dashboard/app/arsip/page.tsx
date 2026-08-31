'use client'

import { useEffect, useMemo, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { WoArchive, CITY_LABEL, ALL_CITIES, CityKey, COLUMN_DEFS } from '@/lib/types'
import { statusColor } from '@/lib/statusStyle'

function formatCell(value: unknown, type: string): string {
  if (value === null || value === undefined || value === '') return '-'
  if (type === 'date') {
    const d = new Date(value as string)
    if (isNaN(d.getTime())) return String(value)
    return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
  }
  return String(value)
}

export default function ArsipPage() {
  const [data, setData] = useState<WoArchive[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [cityFilter, setCityFilter] = useState<CityKey | 'ALL'>('ALL')

  useEffect(() => {
    const load = async () => {
      setIsLoading(true)
      const { data, error } = await supabase
        .from('wo_archive')
        .select('*')
        .order('updated_at', { ascending: false })
      if (!error && data) setData(data as WoArchive[])
      setIsLoading(false)
    }
    load()
  }, [])

  const filtered = useMemo(() => {
    return data.filter((row) => {
      const matchSearch =
        search.trim() === '' ||
        row.incident.toLowerCase().includes(search.toLowerCase()) ||
        (row.customer_name ?? '').toLowerCase().includes(search.toLowerCase())
      const matchCity = cityFilter === 'ALL' || row.kota === cityFilter
      return matchSearch && matchCity
    })
  }, [data, search, cityFilter])

  return (
    <main className="min-h-screen px-6 py-6 sm:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Arsip Tiket</h1>
        <p className="mt-1 text-sm font-medium text-gray-600">
          Tiket berstatus Close yang sudah lewat 24 jam, dari semua kota
        </p>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Cari incident / nama pelanggan..."
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-300"
        />
        <select
          value={cityFilter}
          onChange={(e) => setCityFilter(e.target.value as CityKey | 'ALL')}
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-300"
        >
          <option value="ALL">Semua Kota</option>
          {ALL_CITIES.map((c) => (
            <option key={c} value={c}>{CITY_LABEL[c]}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Memuat data arsip...</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-gray-500">Tidak ada tiket arsip yang cocok.</p>
      ) : (
        <div className="h-[calc(100vh-260px)] overflow-auto rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full border-collapse text-sm">
            <thead className="sticky top-0 z-10 border-b border-gray-200 bg-gray-50">
              <tr>
                <th className="border-r border-gray-100 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wide text-gray-700">
                  Kota
                </th>
                {COLUMN_DEFS.filter((c) => c.type !== 'ttr' && c.type !== 'ttr_manja').map((col) => (
                  <th
                    key={col.key}
                    className="whitespace-nowrap border-r border-gray-100 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wide text-gray-700"
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((row) => (
                <tr key={`${row.kota}-${row.id}`} className="hover:bg-gray-50">
                  <td className="border-r border-gray-100 px-3 py-2 font-medium text-gray-700">
                    {CITY_LABEL[row.kota]}
                  </td>
                  {COLUMN_DEFS.filter((c) => c.type !== 'ttr' && c.type !== 'ttr_manja').map((col) => {
                    if (col.type === 'status') {
                      return (
                        <td key={col.key} className="border-r border-gray-100 px-3 py-2">
                          <span className={`inline-block whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusColor[row.status]}`}>
                            {row.status}
                          </span>
                        </td>
                      )
                    }
                    const value = row[col.key as keyof WoArchive]
                    return (
                      <td key={col.key} className="border-r border-gray-100 px-3 py-2 text-gray-800">
                        <span className="block max-w-[220px] truncate">{formatCell(value, col.type)}</span>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}