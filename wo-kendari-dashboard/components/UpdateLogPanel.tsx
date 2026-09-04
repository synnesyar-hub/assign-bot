// components/UpdateLogPanel.tsx
'use client'

import { useState, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import { submitLogUpdate } from '@/lib/logUtils'
import { usePresence } from '@/context/PresenceContext'
import 'react-quill-new/dist/quill.snow.css'

const ReactQuill = dynamic(() => import('react-quill-new'), { ssr: false })

const RETRY_COOLDOWN_MS = 15_000
const SUCCESS_MESSAGE_MS = 5_000
const ACCEPTED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/gif']

const QUILL_MODULES = {
  toolbar: [['bold', 'italic', 'underline'], [{ list: 'ordered' }, { list: 'bullet' }], ['clean']],
}

interface UpdateLogPanelProps {
  table: string
  incident: string
  ticketId: number
  isSynced: boolean
  logSyncError?: string | null
  onSuccess?: () => void
}

function isQuillEmpty(html: string): boolean {
  return html.replace(/<[^>]*>/g, '').trim() === ''
}

export default function UpdateLogPanel({ table, incident, ticketId, isSynced, logSyncError, onSuccess }: UpdateLogPanelProps) {
  const { setEditing } = usePresence()

  const [summary, setSummary] = useState('')
  const [description, setDescription] = useState('')
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [photoPreview, setPhotoPreview] = useState<string | null>(null)
  const [isDraggingOver, setIsDraggingOver] = useState(false)

  const [summaryLocked, setSummaryLocked] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(null)
  const [justSucceeded, setJustSucceeded] = useState(false)
  const [, forceTick] = useState(0)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null)
  const successTimerRef = useRef<NodeJS.Timeout | null>(null)
  const wasSyncedRef = useRef(isSynced)

  // Reset & lock ulang tiap kali ticket yang dibuka berganti
  useEffect(() => {
    setSummary('')
    setDescription('')
    setPhotoFile(null)
    setPhotoPreview(null)
    setError(null)
    setSummaryLocked(true)
    setCooldownUntil(null)
    setJustSucceeded(false)
    wasSyncedRef.current = isSynced

    const delay = 1000 + Math.random() * 2000
    const t = setTimeout(() => setSummaryLocked(false), delay)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incident])

  // Worker konfirmasi log tersinkron -- tampilkan pesan sukses sebentar
  useEffect(() => {
    if (isSynced && !wasSyncedRef.current) {
      setCooldownUntil(null)
      setJustSucceeded(true)
      if (successTimerRef.current) clearTimeout(successTimerRef.current)
      successTimerRef.current = setTimeout(() => setJustSucceeded(false), SUCCESS_MESSAGE_MS)
    }
    wasSyncedRef.current = isSynced
  }, [isSynced])

  useEffect(() => {
    return () => {
      if (successTimerRef.current) clearTimeout(successTimerRef.current)
      if (heartbeatRef.current) clearInterval(heartbeatRef.current)
    }
  }, [])

  // Re-render tiap detik selama cooldown supaya countdown update
  useEffect(() => {
    if (cooldownUntil === null) return
    const interval = setInterval(() => forceTick((n) => n + 1), 1000)
    return () => clearInterval(interval)
  }, [cooldownUntil])

  const startHeartbeat = () => {
    setEditing(String(ticketId), 'log')
    heartbeatRef.current = setInterval(() => setEditing(String(ticketId), 'log'), 3000)
  }
  const stopHeartbeat = () => {
    if (heartbeatRef.current) clearInterval(heartbeatRef.current)
    heartbeatRef.current = null
    setEditing(null, null)
  }

  const processFile = (file: File | null) => {
    setPhotoFile(file)
    if (photoPreview) URL.revokeObjectURL(photoPreview)
    setPhotoPreview(file ? URL.createObjectURL(file) : null)
  }

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    processFile(e.target.files?.[0] ?? null)
  }

  const handleRemovePhoto = () => {
    setPhotoFile(null)
    if (photoPreview) URL.revokeObjectURL(photoPreview)
    setPhotoPreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleDragOver = (e: React.DragEvent<HTMLLabelElement | HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (submitting) return
    setIsDraggingOver(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLLabelElement | HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDraggingOver(false)
  }

  const handleDrop = (e: React.DragEvent<HTMLLabelElement | HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDraggingOver(false)
    if (submitting) return

    // DEBUG SEMENTARA — lihat apa isi dataTransfer
    console.log('dataTransfer.files:', e.dataTransfer.files)
    console.log('dataTransfer.files.length:', e.dataTransfer.files.length)
    console.log('dataTransfer.types:', e.dataTransfer.types)
    console.log('dataTransfer.items:', e.dataTransfer.items)
    console.log('dataTransfer.items.length:', e.dataTransfer.items.length)
    if (e.dataTransfer.files.length > 0) {
    console.log('file[0] name:', e.dataTransfer.files[0].name)
    console.log('file[0] size:', e.dataTransfer.files[0].size)
    console.log('file[0] type:', e.dataTransfer.files[0].type)
    }

    const file = e.dataTransfer.files?.[0]
    if (!file) return

    if (!ACCEPTED_PHOTO_TYPES.includes(file.type)) {
      setError('Format foto harus JPEG, PNG, atau GIF')
      return
    }
    setError(null)
    processFile(file)
  }

  const secondsLeft = cooldownUntil ? Math.max(0, Math.ceil((cooldownUntil - Date.now()) / 1000)) : 0
  const inCooldown = secondsLeft > 0

  const handleSubmit = async () => {
    if (!summary.trim() || submitting || inCooldown) return
    setSubmitting(true)
    setError(null)
    setJustSucceeded(false)
    try {
      await submitLogUpdate(table, incident, summary.trim(), description, photoFile)
      setSummary('')
      setDescription('')
      handleRemovePhoto()
      setSummaryLocked(true)
      const delay = 1000 + Math.random() * 2000
      setTimeout(() => setSummaryLocked(false), delay)
      setCooldownUntil(Date.now() + RETRY_COOLDOWN_MS)
      onSuccess?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Gagal menyimpan log')
    } finally {
      setSubmitting(false)
      stopHeartbeat()
    }
  }

  let statusMessage: { text: string; className: string } | null = null
  if (submitting) {
    statusMessage = { text: 'Mengirim...', className: 'text-gray-500 font-medium' }
  } else if (justSucceeded) {
    statusMessage = { text: 'Log berhasil dikirim & tersinkron ke Insera', className: 'text-green-700 font-semibold' }
  } else if (inCooldown) {
    statusMessage = { text: `Menunggu worker memproses... (${secondsLeft}s)`, className: 'text-gray-600 font-semibold' }
  } else if (!isSynced && logSyncError) {
    statusMessage = { text: `Gagal sync: ${logSyncError}`, className: 'text-red-700 font-semibold' }
  }

    return (
    <div>
      <style jsx global>{`
        .ql-toolbar.ql-snow {
          border-color: #9ca3af;
          border-width: 2px;
        }
        .ql-toolbar.ql-snow button svg .ql-stroke {
          stroke: #374151;
        }
        .ql-toolbar.ql-snow button svg .ql-fill {
          fill: #374151;
        }
        .ql-toolbar.ql-snow button:hover svg .ql-stroke,
        .ql-toolbar.ql-snow button.ql-active svg .ql-stroke {
          stroke: #2563eb;
        }
        .ql-toolbar.ql-snow button:hover svg .ql-fill,
        .ql-toolbar.ql-snow button.ql-active svg .ql-fill {
          fill: #2563eb;
        }
        .ql-container.ql-snow {
          border-color: #9ca3af;
          border-width: 2px;
          border-top: none;
        }
        .ql-editor {
          color: #111827;
          font-size: 14px;
        }
        .ql-editor.ql-blank::before {
          color: #6b7280;
          font-style: normal;
        }
      `}</style>

      <label className="text-sm font-bold uppercase tracking-wide text-gray-700">Log Update</label>

      <div className="mt-2 grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-semibold text-gray-600">Summary</label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            onFocus={() => !summaryLocked && startHeartbeat()}
            onBlur={stopHeartbeat}
            disabled={summaryLocked || submitting}
            placeholder={summaryLocked ? 'Mohon tunggu...' : 'Ringkasan update...'}
            rows={8}
            className={`mt-1 w-full resize-none rounded-md border-2 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-100 ${
                summaryLocked ? 'cursor-not-allowed border-gray-300 bg-gray-100 text-gray-400' : 'border-gray-400 focus:border-blue-400'
            }`}
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-600">Description</label>
          <div className="mt-1" onFocus={startHeartbeat} onBlur={stopHeartbeat}>
            <ReactQuill
              theme="snow"
              value={description}
              onChange={setDescription}
              readOnly={submitting}
              modules={QUILL_MODULES}
              placeholder="Detail tambahan..."
              className="[&_.ql-container]:min-h-[190px] [&_.ql-container]:text-sm"
            />
          </div>
        </div>
      </div>

      <div className="mt-4">
        <label className="text-xs font-semibold text-gray-600">Foto</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif"
          onChange={handlePhotoChange}
          disabled={submitting}
          className="hidden"
          id="log-photo-input"
        />
        {photoPreview ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative mt-1 h-48 w-full overflow-hidden rounded-md border-2 transition-colors ${
              isDraggingOver ? 'border-blue-500' : 'border-gray-400'
            }`}
          >
            <img src={photoPreview} alt="Preview" className="h-full w-full object-cover" />
            {isDraggingOver && (
              <div className="absolute inset-0 flex items-center justify-center bg-blue-600/70 text-sm font-semibold text-white">
                Lepas untuk ganti foto
              </div>
            )}
            <button
              type="button"
              onClick={handleRemovePhoto}
              disabled={submitting}
              className="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-1 text-xs text-white"
            >
              ✕
            </button>
          </div>
        ) : (
          <label
            htmlFor="log-photo-input"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`mt-1 flex h-48 w-full cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed text-sm font-medium transition-colors hover:bg-gray-50 ${
              isDraggingOver ? 'border-blue-500 bg-blue-50 text-blue-600' : 'border-gray-400 text-gray-500'
            }`}
          >
            {isDraggingOver ? 'Lepas untuk unggah foto' : 'Tap atau seret foto ke sini'}
          </label>
        )}
      </div>

      {error && <p className="mt-2 text-xs font-medium text-red-600">{error}</p>}

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button
          onClick={handleSubmit}
          disabled={submitting || summaryLocked || inCooldown || !summary.trim()}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          {submitting ? 'Menyimpan...' : 'Simpan Log'}
        </button>
        {statusMessage && <span className={`text-xs ${statusMessage.className}`}>{statusMessage.text}</span>}
      </div>
    </div>
  )
}