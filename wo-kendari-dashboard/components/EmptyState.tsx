'use client'

interface Props {
  title: string
  description?: string
  icon?: 'empty' | 'success'
}

export default function EmptyState({ title, description, icon = 'empty' }: Props) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-white/60 px-6 py-12 text-center">
      <div
        className={`mb-3 flex h-12 w-12 items-center justify-center rounded-full ${
          icon === 'success' ? 'bg-emerald-50 text-emerald-500' : 'bg-gray-100 text-gray-400'
        }`}
      >
        <span className="text-2xl">{icon === 'success' ? '✓' : '—'}</span>
      </div>
      <p className="text-sm font-medium text-gray-700">{title}</p>
      {description && <p className="mt-1 text-xs text-gray-500">{description}</p>}
    </div>
  )
}