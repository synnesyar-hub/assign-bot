/* assign-bot/wo-kendari-dashboard/lib/statusStyle.ts */

import { WoStatus } from './types'

export const statusColor: Record<WoStatus, string> = {
  OPEN: 'bg-red-50 text-red-600 border-red-200',
  MONITORING: 'bg-amber-50 text-amber-600 border-amber-200',
  GAMAS: 'bg-orange-50 text-orange-600 border-orange-200',
  KENDALA: 'bg-purple-50 text-purple-600 border-purple-200',
  PENDING: 'bg-blue-50 text-blue-600 border-blue-200',
  'CLOSE CROSSCHECK': 'bg-slate-50 text-slate-600 border-slate-200',
  CLOSE: 'bg-emerald-50 text-emerald-600 border-emerald-200',
}

export const statusAccent: Record<WoStatus, string> = {
  OPEN: 'border-l-red-400',
  MONITORING: 'border-l-amber-400',
  GAMAS: 'border-l-orange-400',
  KENDALA: 'border-l-purple-400',
  PENDING: 'border-l-blue-400',
  'CLOSE CROSSCHECK': 'border-l-slate-300',
  CLOSE: 'border-l-emerald-400',
}

export const ACTIVE_STATUSES: WoStatus[] = ['OPEN', 'MONITORING', 'GAMAS', 'KENDALA', 'PENDING']
export const INACTIVE_STATUSES: WoStatus[] = ['CLOSE CROSSCHECK', 'CLOSE']