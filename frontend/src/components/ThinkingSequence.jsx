import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

const FULL_STAGES = [
  {
    key: 'extract',
    label: 'Stage 1 · language model',
    detail: 'Reading your description',
  },
  {
    key: 'predict',
    label: 'Stage 2 · trained regressor',
    detail: 'Computing the estimate',
  },
  {
    key: 'explain',
    label: 'Stage 3 · language model',
    detail: 'Writing the explanation',
  },
]

const EXTRACT_STAGES = [FULL_STAGES[0]]

export default function ThinkingSequence({ mode = 'full' }) {
  const stages = mode === 'extract' ? EXTRACT_STAGES : FULL_STAGES
  const [active, setActive] = useState(0)

  useEffect(() => {
    setActive(0)
    if (stages.length === 1) return undefined

    const timers = [
      setTimeout(() => setActive(1), 600),
      setTimeout(() => setActive(2), 1250),
    ]

    return () => timers.forEach(clearTimeout)
  }, [mode, stages.length])

  return (
    <div className="mx-auto max-w-6xl px-6 pb-32">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="rounded-[28px] border border-seam bg-surface/70 p-10 md:p-14"
      >
        <div className="flex items-center gap-3 text-[11px] uppercase tracking-eyebrow text-muted">
          <span className="inline-block h-px w-8 bg-brass" />
          {mode === 'extract'
            ? 'Stage 1 is reading the description'
            : 'The assistant is thinking'}
        </div>

        <div className="mt-10 grid gap-7">
          {stages.map((stage, index) => {
            const state =
              index < active ? 'done' : index === active ? 'active' : 'idle'

            return (
              <motion.div
                key={stage.key}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.15, duration: 0.5 }}
                className="flex items-center gap-6"
              >
                <div className="relative flex h-10 w-10 shrink-0 items-center justify-center">
                  {state === 'active' && (
                    <motion.span
                      className="absolute inset-0 rounded-full border border-terracotta/70"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.9, 0, 0.9] }}
                      transition={{ duration: 1.6, repeat: Infinity, ease: 'easeOut' }}
                    />
                  )}
                  <span
                    className={`h-2.5 w-2.5 rounded-full transition-colors duration-500 ${
                      state === 'done'
                        ? 'bg-teal'
                        : state === 'active'
                          ? 'bg-terracotta'
                          : 'bg-seam'
                    }`}
                  />
                </div>

                <div className="flex-1">
                  <div
                    className={`font-display text-2xl transition-colors duration-500 md:text-4xl ${
                      state === 'idle' ? 'text-muted/40' : 'text-ink'
                    }`}
                  >
                    {stage.detail}
                  </div>
                  <div className="mt-1 text-[11px] uppercase tracking-eyebrow text-muted">
                    {stage.label}
                  </div>
                </div>

                {state === 'done' && (
                  <motion.span
                    initial={{ opacity: 0, x: -4 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="hidden text-[11px] uppercase tracking-eyebrow text-teal md:inline"
                  >
                    Complete
                  </motion.span>
                )}
              </motion.div>
            )
          })}
        </div>
      </motion.div>
    </div>
  )
}
