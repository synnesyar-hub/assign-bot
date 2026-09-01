// components/RecapAllButton.tsx
'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { syncKendalaForKota } from '@/lib/syncKendala'
import { ALL_CITIES, CITY_SYNC_FN, CityKey } from '@/lib/types'

interface Props {
  onDone: () => void
}

export default function RecapAllButton({ onDone }: Props) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleClick = async () => {
    setLoading(true)
    setResult(null)

    let totalSynced = 0
    const failedKota: string[] = []

    for (const kota of ALL_CITIES) {
      try {
        const { data, error } = await supabase.rpc(CITY_SYNC_FN[kota])
        if (error) throw error
        totalSynced += Number(data ?? 0)

        await syncKendalaForKota(supabase, kota as CityKey)
      } catch {
        failedKota.push(kota)
      }
    }

    setLoading(false)
    onDone()

    if (failedKota.length > 0) {
      setResult(`Selesai sebagian — gagal di: ${failedKota.join(', ')}`)
    } else {
      setResult(`Berhasil, ${totalSynced} tiket disinkronkan (semua kota).`)
    }
    setTimeout(() => setResult(null), 4000)
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleClick}
        disabled={loading}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Merekap...' : '↻ Rekap Semua Tiket'}
      </button>
      {result && <span className="text-xs text-gray-500">{result}</span>}
    </div>
  )
}