import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles } from 'lucide-react'

const EXAMPLES = [
  {
    title: 'OldTown ranch',
    text: '3 bedroom ranch in OldTown, built 1960, 1-car garage, fair condition, 1100 sqft',
  },
  {
    title: 'NridgHt luxury',
    text: 'Luxury 2-story in NridgHt, 2500 sqft, 4 beds, 3 full baths, built 2006, excellent quality, 3-car garage, fireplace',
  },
  {
    title: 'Small Edwards bungalow',
    text: 'Small bungalow in Edwards, 2 bedrooms, 1 bath, old and worn, about 900 sqft, no basement',
  },
  {
    title: 'CollgCr 1.5-story',
    text: 'CollgCr 1.5-story, 3 bed, 2 full bath, built 1998, 2-car garage, finished basement, good condition',
  },
]

export default function QueryComposer({ onAnalyze, disabled, initialValue }) {
  const [value, setValue] = useState(initialValue || '')

  // Keep local state in sync if the parent replays a previous query
  // (e.g. after an error -> retry cycle).
  useEffect(() => {
    if (initialValue !== undefined) setValue(initialValue)
  }, [initialValue])

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onAnalyze(trimmed)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      submit()
    }
  }

  const canSubmit = !disabled && value.trim().length > 0

  return (
    <section className="mx-auto max-w-6xl px-6 pb-20">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative rounded-[28px] bg-surface border border-seam shadow-lift p-8 md:p-10"
      >
        <div className="flex items-center justify-between mb-6">
          <span className="flex items-center gap-2 text-[11px] uppercase tracking-eyebrow text-muted">
            <Sparkles className="h-3.5 w-3.5 text-terracotta" />
            The description
          </span>
          <span className="hidden md:inline text-[11px] uppercase tracking-eyebrow text-muted">
            ⌘ + Enter to analyze
          </span>
        </div>

        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="A two-story in NridgHt, four bedrooms, built in 2006, finished basement, excellent quality…"
          rows={3}
          disabled={disabled}
          className="w-full resize-none bg-transparent font-display font-light text-2xl md:text-4xl leading-[1.2] text-ink placeholder:text-muted/50 disabled:opacity-60"
        />

        <div className="mt-10 flex flex-col md:flex-row md:items-end md:justify-between gap-6">
          <div className="flex flex-col gap-3">
            <span className="text-[11px] uppercase tracking-eyebrow text-muted">
              Or start from a sample description
            </span>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.title}
                  type="button"
                  onClick={() => setValue(ex.text)}
                  disabled={disabled}
                  className="px-3.5 py-1.5 text-xs text-ink/80 border border-seam rounded-full bg-canvas/60 hover:border-brass hover:text-ink hover:bg-canvas transition disabled:opacity-50"
                >
                  {ex.title}
                </button>
              ))}
            </div>
          </div>

          <motion.button
            type="button"
            onClick={submit}
            disabled={!canSubmit}
            whileTap={{ scale: 0.97 }}
            className="group inline-flex items-center gap-4 px-7 py-4 rounded-full bg-terracotta text-canvas shadow-cta disabled:opacity-40 disabled:shadow-none hover:bg-[#b26b49] transition-colors"
          >
            <span className="text-[11px] uppercase tracking-eyebrow">
              Analyze the description
            </span>
            <span className="relative flex items-center justify-center h-7 w-7 rounded-full bg-canvas/15">
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </span>
          </motion.button>
        </div>
      </motion.div>
    </section>
  )
}
