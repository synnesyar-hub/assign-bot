'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ALL_CITIES, CITY_LABEL } from '@/lib/types'

interface ItemProps {
  label: string
  href: string
  active: boolean
}

function Item({ label, href, active }: ItemProps) {
  return (
    <Link
      href={href}
      className={`block w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors ${
        active ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
      }`}
    >
      {label}
    </Link>
  )
}

function SubItem({ label, href, active }: ItemProps) {
  return (
    <Link
      href={href}
      className={`block w-full rounded-md py-1.5 pl-3 pr-3 text-left text-[13px] font-medium transition-colors ${
        active
          ? 'border-l-2 border-blue-400 bg-white/5 text-white'
          : 'border-l-2 border-transparent text-gray-500 hover:border-white/20 hover:text-gray-300'
      }`}
    >
      {label}
    </Link>
  )
}

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="flex w-60 shrink-0 flex-col bg-[#14161a] px-4 py-6">
      <div className="px-2 text-lg font-bold text-white">Ops Center</div>
      <p className="px-2 text-xs text-gray-500">Multi-Kota</p>

      <nav className="mt-8 space-y-1">
        <Item label="Board Insiden" href="/" active={pathname === '/'} />

        <div className="pt-4">
          <p className="px-3 text-[11px] font-semibold uppercase tracking-wide text-gray-500">
            Semua Tiket
          </p>
          <div className="mt-2 ml-2 space-y-0.5 border-l border-white/10 pl-1">
            {ALL_CITIES.map((city) => (
              <SubItem
                key={city}
                label={CITY_LABEL[city]}
                href={`/tiket/${city}`}
                active={pathname === `/tiket/${city}`}
              />
            ))}
          </div>
        </div>

        <div className="pt-3">
          <Item label="Arsip Tiket" href="/arsip" active={pathname === '/arsip'} />
        </div>
      </nav>

      <div className="mt-auto rounded-xl bg-white/5 p-3">
        <p className="text-xs font-medium text-gray-400">Shift aktif</p>
        <p className="text-sm font-semibold text-white">08:00 – 16:00</p>
      </div>
    </aside>
  )
}