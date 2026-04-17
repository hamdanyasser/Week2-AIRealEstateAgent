import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

// Per-stage metadata + the ambient "stream" of sub-steps that get
// ticker-taped inside the stage while it's active. These lines are
// purely narrative — they describe what the real pipeline is doing
// (Stage 1 → predictor → Stage 2) so the UI makes the AI *observable*.
const FULL_STAGES = [
  {
    key: 'extract',
    label: 'Stage 1 · language model',
    detail: 'Reading your description',
    duration: 900,
    stream: [
      'parsing natural language',
      'identifying dataset features',
      'validating with schema',
      'extraction ready',
    ],
  },
  {
    key: 'predict',
    label: 'Stage 2 · trained regressor',
    detail: 'Computing the estimate',
    duration: 700,
    stream: [
      'loading random forest · 100 trees',
      'imputing missing fields from training medians',
      'scoring ensemble',
      'aggregating estimate',
    ],
  },
  {
    key: 'explain',
    label: 'Stage 3 · language model',
    detail: 'Writing the explanation',
    duration: 900,
    stream: [
      'grounding in training statistics',
      'composing the rationale',
      'final pass',
    ],
  },
]

const EXTRACT_STAGES = [FULL_STAGES[0]]

// Tiny presentational component: a horizontal progress bar that fills
// smoothly from 0→1 over the stage's duration while active, and snaps
// full on completion. We keyframe the width with Framer Motion so the
// fill is GPU-friendly and restarts cleanly when `state` flips.
function StageBar({ state, duration }) {
  const target = state === 'idle' ? 0 : 1
  return (
    <div className="relative mt-3 h-[2px] w-full overflow-hidden rounded-full bg-seam/60">
      <motion.div
        key={state}
        initial={{ width: state === 'done' ? '100%' : '0%' }}
        animate={{ width: `${target * 100}%` }}
        transition={{
          duration: state === 'active' ? duration / 1000 : 0.35,
          ease: state === 'active' ? 'easeInOut' : [0.22, 1, 0.36, 1],
        }}
        className={`h-full ${
          state === 'done' ? 'bg-teal' : 'bg-terracotta'
        }`}
      />
    </div>
  )
}

// Scrolling ticker of sub-steps that fades lines in/out while the stage
// is active. Only renders during `active`; collapses on `done`/`idle`.
function StageStream({ lines, active }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!active) {
      setIndex(0)
      return undefined
    }
    const step = Math.max(250, Math.floor(2400 / lines.length))
    const timers = lines.map((_, i) =>
      setTimeout(() => setIndex(i), i * step)
    )
    return () => timers.forEach(clearTimeout)
  }, [active, lines])

  if (!active) return null

  return (
    <div className="mt-3 h-5 overflow-hidden font-mono text-[11px] text-muted">
      <AnimatePresence mode="wait">
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.35 }}
          className="flex items-center gap-2"
        >
          <span className="text-terracotta">›</span>
          <span>{lines[index]}</span>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

// Tiny elapsed-ms counter: starts at 0 when the stage goes active,
// freezes at its last value when the stage completes. Updates every
// animation frame via rAF so it feels like a live instrument.
function Elapsed({ state, startedAt, frozen }) {
  const [ms, setMs] = useState(0)

  useEffect(() => {
    if (state !== 'active' || startedAt == null) return undefined
    let raf
    const tick = () => {
      setMs(Math.round(performance.now() - startedAt))
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [state, startedAt])

  if (state === 'idle') return null
  const value = state === 'done' ? frozen : ms
  return (
    <span className="font-mono text-[11px] tabular text-muted">
      {value} ms
    </span>
  )
}

export default function ThinkingSequence({ mode = 'full' }) {
  const stages = mode === 'extract' ? EXTRACT_STAGES : FULL_STAGES
  const [active, setActive] = useState(0)
  const [elapsedAt, setElapsedAt] = useState(() => performance.now())
  const frozenRef = useRef({})

  // Advance through stages on the durations declared above. We snapshot
  // each stage's final elapsed-ms into frozenRef at handoff so the
  // "done" pill shows a stable number instead of the live counter.
  useEffect(() => {
    setActive(0)
    setElapsedAt(performance.now())
    frozenRef.current = {}

    if (stages.length === 1) return undefined

    const timers = []
    let accumulated = 0
    stages.slice(0, -1).forEach((stage, i) => {
      accumulated += stage.duration
      timers.push(
        setTimeout(() => {
          frozenRef.current[i] = stage.duration
          setActive(i + 1)
          setElapsedAt(performance.now())
        }, accumulated)
      )
    })

    return () => timers.forEach(clearTimeout)
  }, [mode, stages.length])

  return (
    <div className="mx-auto max-w-6xl px-6 pb-32">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="glass rounded-[28px] p-10 md:p-14"
      >
        <div className="flex items-center gap-3 text-[11px] uppercase tracking-eyebrow text-muted">
          <span className="inline-block h-px w-8 bg-brass" />
          {mode === 'extract'
            ? 'Stage 1 is reading the description'
            : 'The assistant is thinking'}
        </div>

        {/* Connected vertical timeline: each stage row shares a gradient
            rail on the left that reflects completion state. */}
        <div className="relative mt-10">
          <div
            className="absolute left-[19px] top-2 bottom-2 w-px bg-gradient-to-b from-seam via-seam to-seam/30"
            aria-hidden
          />

          <div className="grid gap-10">
            {stages.map((stage, index) => {
              const state =
                index < active ? 'done' : index === active ? 'active' : 'idle'

              return (
                <motion.div
                  key={stage.key}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.15, duration: 0.5 }}
                  className="relative flex items-start gap-6"
                >
                  <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center">
                    {state === 'active' && (
                      <motion.span
                        className="absolute inset-0 rounded-full border border-terracotta/70"
                        animate={{ scale: [1, 1.5, 1], opacity: [0.9, 0, 0.9] }}
                        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeOut' }}
                      />
                    )}
                    {/* Solid dot sits on the rail; color flips per state. */}
                    <span
                      className={`h-3 w-3 rounded-full ring-4 ring-canvas transition-colors duration-500 ${
                        state === 'done'
                          ? 'bg-teal'
                          : state === 'active'
                            ? 'bg-terracotta'
                            : 'bg-seam'
                      }`}
                    />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-baseline justify-between gap-4">
                      <div
                        className={`font-display text-2xl transition-colors duration-500 md:text-3xl ${
                          state === 'idle' ? 'text-muted/40' : 'text-ink'
                        }`}
                      >
                        {stage.detail}
                      </div>
                      <Elapsed
                        state={state}
                        startedAt={state === 'active' ? elapsedAt : null}
                        frozen={frozenRef.current[index] ?? stage.duration}
                      />
                    </div>

                    <div className="mt-1 flex items-center gap-3 text-[11px] uppercase tracking-eyebrow text-muted">
                      <span>{stage.label}</span>
                      {state === 'done' && (
                        <motion.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="text-teal"
                        >
                          · complete
                        </motion.span>
                      )}
                    </div>

                    <StageBar state={state} duration={stage.duration} />
                    <StageStream lines={stage.stream} active={state === 'active'} />
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
