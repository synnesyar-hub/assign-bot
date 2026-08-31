'use client'

import { CityKey, CITY_LABEL, ALL_CITIES } from '@/lib/types'

interface Props {
  active: CityKey | 'ALL'
  onChange: (value: CityKey | 'ALL') => void
}

export default function CityTabs({ active, onChange }: Props) {
  const options: { key: CityKey | 'ALL'; label: string }[] = [
    { key: 'ALL', label: 'Semua Kota' },
    ...ALL_CITIES.map((c) => ({ key: c, label: CITY_LABEL[c] })),
  ]

  return (
    <div className="inline-flex rounded-xl bg-gray-100 p-1">
      {options.map((opt) => (
        <button
          key={opt.key}
          onClick={() => onChange(opt.key)}
          className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition-colors ${
            active === opt.key
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}