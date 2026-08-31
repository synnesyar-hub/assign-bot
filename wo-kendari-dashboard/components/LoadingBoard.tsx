'use client'

export default function LoadingBoard() {
  const columns = 5
  return (
    <div className="grid grid-cols-5 gap-3">
      {Array.from({ length: columns }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-2xl bg-white/60 p-3">
          <div className="mb-3 h-4 w-16 rounded bg-gray-200" />
          <div className="space-y-2">
            <div className="h-16 rounded-xl bg-gray-100" />
            <div className="h-16 rounded-xl bg-gray-100" />
          </div>
        </div>
      ))}
    </div>
  )
}