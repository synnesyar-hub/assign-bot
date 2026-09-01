'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { syncKendalaForKota } from '@/lib/syncKendala'
import { CityKey } from '@/lib/types'

interface RecapButtonProps {
  syncFn: string
  kota: CityKey
  onDone: () => void
}

export default function RecapButton({ syncFn, kota, onDone }: RecapButtonProps) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleClick = async () => {
    setLoading(true)
    setResult(null)

    const { data, error } = await supabase.rpc(syncFn)

    if (error) {
      setLoading(false)
      setResult(`Gagal rekap: ${error.message}`)
      return
    }

    try {
      await syncKendalaForKota(supabase, kota)
    } catch (kendalaErr) {
      setLoading(false)
      const message =
       kendalaErr instanceof Error
         ? kendalaErr.message
         : typeof kendalaErr === 'object' && kendalaErr !== null && 'message' in kendalaErr
           ? String((kendalaErr as { message: unknown }).message)
           : String(kendalaErr)
      setResult(`Rekap tiket berhasil, tapi gagal hitung Kendala: ${message}`)
      onDone()
      setTimeout(() => setResult(null), 4000)
      return
    }

    setLoading(false)
    setResult(`Berhasil, ${data ?? 0} tiket disinkronkan.`)
    onDone()

    // pesan hasil hilang otomatis setelah beberapa detik
    setTimeout(() => setResult(null), 4000)
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleClick}
        disabled={loading}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Merekap...' : '↻ Rekap Tiket'}
      </button>
      {result && <span className="text-xs text-gray-500">{result}</span>}
    </div>
  )
}