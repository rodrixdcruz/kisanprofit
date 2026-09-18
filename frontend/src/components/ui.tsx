import { ReactNode } from 'react'

export function Button({ children, onClick, type = 'button', variant = 'primary',
                         className = '', disabled }: {
  children: ReactNode; onClick?: () => void; type?: 'button' | 'submit'
  variant?: 'primary' | 'ghost' | 'danger'; className?: string; disabled?: boolean
}) {
  const styles = {
    primary: 'bg-green-700 text-white hover:bg-green-800 disabled:opacity-50',
    ghost: 'border border-green-700 text-green-800 hover:bg-green-50',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  }[variant]
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      className={`btn-tap rounded-xl px-4 py-2 text-base font-semibold transition ${styles} ${className}`}>
      {children}
    </button>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl bg-white p-4 shadow-sm ring-1 ring-black/5 ${className}`}>{children}</div>
}

export function StatCard({ label, value, sub, accent }: {
  label: string; value: string; sub?: string; accent?: 'green' | 'red' | 'amber'
}) {
  const color = accent === 'red' ? 'text-red-600' : accent === 'amber' ? 'text-amber-600' : 'text-green-700'
  return (
    <Card>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-gray-400">{sub}</p>}
    </Card>
  )
}

export function Modal({ open, onClose, title, children }: {
  open: boolean; onClose: () => void; title: string; children: ReactNode
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-lg rounded-2xl bg-white p-5" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-bold">{title}</h3>
          <button onClick={onClose} className="text-2xl leading-none text-gray-400">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function BottomSheet({ open, onClose, title, children }: {
  open: boolean; onClose: () => void; title: string; children: ReactNode
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 bg-black/40" onClick={onClose}>
      <div className="fixed inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-3xl bg-white p-5"
           onClick={(e) => e.stopPropagation()}>
        <div className="mx-auto mb-3 h-1.5 w-12 rounded-full bg-gray-300" />
        <h3 className="mb-3 text-lg font-bold">{title}</h3>
        {children}
      </div>
    </div>
  )
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  const { label, ...rest } = props
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm font-medium text-gray-600">{label}</span>}
      <input {...rest}
        className="w-full rounded-xl border border-gray-300 px-3 py-2 text-base outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100" />
    </label>
  )
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }) {
  const { label, children, ...rest } = props
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm font-medium text-gray-600">{label}</span>}
      <select {...rest}
        className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 text-base outline-none focus:border-green-600">
        {children}
      </select>
    </label>
  )
}

export function Spinner() {
  return <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-green-200 border-t-green-700" />
}

export function EmptyState({ icon = '🌱', message }: { icon?: string; message: string }) {
  return (
    <div className="py-10 text-center">
      <div className="text-4xl">{icon}</div>
      <p className="mt-2 text-gray-500">{message}</p>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="py-10 text-center">
      <div className="text-4xl">⚠️</div>
      <p className="mt-2 text-red-600">{message}</p>
      {onRetry && <Button variant="ghost" className="mt-3" onClick={onRetry}>Retry</Button>}
    </div>
  )
}

export function Badge({ children, tone = 'green' }: { children: ReactNode; tone?: 'green' | 'amber' | 'gray' | 'red' }) {
  const styles = {
    green: 'bg-green-100 text-green-800', amber: 'bg-amber-100 text-amber-800',
    gray: 'bg-gray-100 text-gray-700', red: 'bg-red-100 text-red-700',
  }[tone]
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${styles}`}>{children}</span>
}
