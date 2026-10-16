import { Link } from 'react-router-dom'
import { Zap, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] flex flex-col items-center justify-center p-6 text-center">
      <div className="h-16 w-16 rounded-[var(--radius-xl)] bg-gradient-to-br from-indigo-500/20 to-violet-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
        <Zap className="h-8 w-8 text-[var(--accent-indigo)]" />
      </div>
      <p className="text-5xl font-bold text-gradient-indigo mb-3">404</p>
      <h1 className="text-xl font-semibold mb-2">Page not found</h1>
      <p className="text-sm text-[var(--text-secondary)] max-w-sm mb-8">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link to="/">
        <Button variant="secondary">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Button>
      </Link>
    </div>
  )
}
