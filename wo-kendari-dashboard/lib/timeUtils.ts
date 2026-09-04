import { WoStatus } from './types'

export function getAgeInHours(reportedDate: string | null): number {
  if (!reportedDate) return 0
  const reported = new Date(reportedDate).getTime()
  const now = Date.now()
  return Math.floor((now - reported) / (1000 * 60 * 60))
}

export function formatAge(hours: number): string {
  if (hours < 1) return 'Baru saja'
  if (hours < 24) return `${hours} jam`
  const days = Math.floor(hours / 24)
  return `${days} hari`
}

export function getSlaLevel(hours: number): 'ok' | 'warning' | 'breach' {
  if (hours >= 24) return 'breach'
  if (hours >= 12) return 'warning'
  return 'ok'
}

export function countThisWeek(data: { reported_date: string | null }[]): number {
  const now = new Date()
  const startOfWeek = new Date(now)
  startOfWeek.setDate(now.getDate() - now.getDay())
  startOfWeek.setHours(0, 0, 0, 0)

  return data.filter((d) => {
    if (!d.reported_date) return false
    return new Date(d.reported_date) >= startOfWeek
  }).length
}

export function countLastWeek(data: { reported_date: string | null }[]): number {
  const now = new Date()
  const startOfThisWeek = new Date(now)
  startOfThisWeek.setDate(now.getDate() - now.getDay())
  startOfThisWeek.setHours(0, 0, 0, 0)

  const startOfLastWeek = new Date(startOfThisWeek)
  startOfLastWeek.setDate(startOfThisWeek.getDate() - 7)

  return data.filter((d) => {
    if (!d.reported_date) return false
    const date = new Date(d.reported_date)
    return date >= startOfLastWeek && date < startOfThisWeek
  }).length
}

export function formatTTR(
  reportedDate: string | null,
  status: string,
  updatedAt: string | null,
  bookingDate: string | null
): string {
  if (!reportedDate) return '-'

  const isClosed = status === 'CLOSE' || status === 'CLOSE CROSSCHECK'
  const end = isClosed && updatedAt ? new Date(updatedAt).getTime() : Date.now()

  let start: number

  if (bookingDate) {
    const booking = new Date(bookingDate).getTime()
    if (Date.now() < booking) {
      // TTR Manja belum habis, TTR belum mulai
      return '00:00:00'
    }
    start = booking
  } else {
    start = new Date(reportedDate).getTime()
  }

  const diffMs = Math.max(0, end - start)
  return formatHms(diffMs)
}

export function getTTRSeconds(
  reportedDate: string | null,
  status: WoStatus,
  updatedAt: string | null,
  bookingDate: string | null
): number {
  const str = formatTTR(reportedDate, status, updatedAt, bookingDate)
  const parts = str.split(':').map((p) => parseInt(p, 10))
  if (parts.length !== 3 || parts.some((p) => isNaN(p))) return 0
  const [h, m, s] = parts
  return h * 3600 + m * 60 + s
}

export function getTTRColorClass(
  reportedDate: string | null,
  status: string,
  updatedAt: string | null,
  bookingDate: string | null
): string {
  const isClosed = status === 'CLOSE' || status === 'CLOSE CROSSCHECK'
  if (isClosed || !reportedDate) return 'text-gray-900'

  let start: number

  if (bookingDate) {
    const booking = new Date(bookingDate).getTime()
    if (Date.now() < booking) return 'text-gray-900' // belum mulai
    start = booking
  } else {
    start = new Date(reportedDate).getTime()
  }

  const hours = (Date.now() - start) / (1000 * 60 * 60)

  if (hours >= 48) return 'text-red-600'
  if (hours >= 24) return 'text-orange-500'
  return 'text-gray-900'
}

export function formatManjaCountdown(bookingDate: string | null): { text: string; overdue: boolean } {
  if (!bookingDate) return { text: '-', overdue: false }

  const target = new Date(bookingDate).getTime()
  const diffMs = target - Date.now()

  if (diffMs <= 0) {
    return { text: formatHms(Math.abs(diffMs)), overdue: true }
  }
  return { text: formatHms(diffMs), overdue: false }
}

export function getManjaSeconds(bookingDate: string | null): number {
  if (!bookingDate) return Number.POSITIVE_INFINITY // tanpa booking_date, taruh di akhir
  const target = new Date(bookingDate).getTime()
  return (target - Date.now()) / 1000
}

function formatHms(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
}

export function getDailyTrendByStatus(
  data: { reported_date: string | null; status: string }[],
  status: string,
  days: number = 6
): { v: number }[] {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const result: { v: number }[] = []

  for (let i = days - 1; i >= 0; i--) {
    const dayStart = new Date(today)
    dayStart.setDate(today.getDate() - i)
    const dayEnd = new Date(dayStart)
    dayEnd.setDate(dayStart.getDate() + 1)

    const count = data.filter((d) => {
      if (!d.reported_date || d.status !== status) return false
      const date = new Date(d.reported_date)
      return date >= dayStart && date < dayEnd
    }).length

    result.push({ v: count })
  }

  return result
}

export function splitDateTime(dateStr: string | null): { date: string; time: string } {
  if (!dateStr) return { date: '-', time: '' }
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return { date: String(dateStr), time: '' }

  const pad = (n: number) => String(n).padStart(2, '0')
  const day = pad(d.getDate())
  const month = pad(d.getMonth() + 1)
  const year = pad(d.getFullYear() % 100)
  const hours = pad(d.getHours())
  const minutes = pad(d.getMinutes())
  const seconds = pad(d.getSeconds())

  return { date: `${day}/${month}/${year}`, time: `${hours}:${minutes}:${seconds}` }
}