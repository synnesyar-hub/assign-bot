'use client'

import { useState, useEffect } from 'react'

interface BookmarkGuardDialogProps {
  bookmarkedBy: string
  onConfirm: () => void
  onCancel: () => void
}

export default function BookmarkGuardDialog({ bookmarkedBy, onConfirm, onCancel }: BookmarkGuardDialogProps) {
  const [secondsLeft, setSecondsLeft] = useState(5)

  useEffect(() => {
    if (secondsLeft <= 0) return
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [secondsLeft])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl">
        <h3 className="text-base font-bold text-gray-900">Tiket Sudah Dibookmark</h3>
        <p className="mt-2 text-sm text-gray-800">
          Tiket ini sudah ditandai (bookmark) oleh <strong>{bookmarkedBy}</strong>. Apakah kamu sudah
          meminta izin untuk mengedit tiket ini?
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Tidak
          </button>
          <button
            onClick={onConfirm}
            disabled={secondsLeft > 0}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {secondsLeft > 0 ? `Ya (tunggu ${secondsLeft}s)` : 'Ya'}
          </button>
        </div>
      </div>
    </div>
  )
}