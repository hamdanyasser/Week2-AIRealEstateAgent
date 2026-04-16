import { motion } from 'framer-motion'
import { AlertTriangle, RotateCcw } from 'lucide-react'

export default function ErrorState({ error, onRetry }) {
  return (
    <section className="mx-auto max-w-3xl px-6 pb-28">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="rounded-[28px] border border-seam bg-surface p-12 text-center shadow-lift"
      >
        <AlertTriangle className="mx-auto h-6 w-6 text-terracotta" />

        <h3 className="mt-5 font-display text-3xl md:text-4xl text-ink">
          The assistant couldn&apos;t answer
        </h3>

        <p className="mt-4 text-muted max-w-md mx-auto leading-relaxed">
          {error?.message ??
            'Something went wrong talking to the backend. Check that the FastAPI service is running on http://localhost:8000 and try again.'}
        </p>

        <button
          type="button"
          onClick={onRetry}
          className="mt-10 inline-flex items-center gap-3 px-6 py-3.5 rounded-full bg-terracotta text-canvas shadow-cta hover:bg-[#b26b49] transition-colors"
        >
          <RotateCcw className="h-4 w-4" />
          <span className="text-[11px] uppercase tracking-eyebrow">Start over</span>
        </button>
      </motion.div>
    </section>
  )
}
