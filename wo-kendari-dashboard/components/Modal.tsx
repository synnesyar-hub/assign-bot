'use client'

interface Props {
  title: string
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
}

export default function Modal({ title, isOpen, onClose, children }: Props) {
  if (!isOpen) return null

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 z-50 max-h-[85vh] w-full max-w-4xl -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl bg-white p-8 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          <button onClick={onClose} className="rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700">
            ✕
          </button>
        </div>
        {children}
      </div>
    </>
  )
}