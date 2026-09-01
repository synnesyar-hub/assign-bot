// app/tiket/[kota]/page.tsx
import { redirect } from 'next/navigation'

export default function LegacyKotaRedirect() {
  redirect('/tiket')
}