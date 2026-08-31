'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'

interface RecapButtonProps {
  syncFn: string
  onDone: () => void
}

export default function RecapButton({ syncFn, onDone }: RecapButtonProps) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleClick = async () => {
    setLoading(true)
    setResult(null)

    const { data, error } = await supabase.rpc(syncFn)

    setLoading(false)

    if (error) {
      setResult(`Gagal rekap: ${error.message}`)
      return
    }

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