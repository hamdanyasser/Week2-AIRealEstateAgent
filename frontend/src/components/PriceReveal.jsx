import { useEffect, useMemo, useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'
import { formatPrice } from '../lib/format.js'
import SectionHeading from './SectionHeading.jsx'

// Easing: cubic ease-out, so the counter decelerates instead of crawling
// linearly up to the target — reads as deliberate rather than mechanical.
function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

// Training-set summary from models/training_stats.json (Step 4).
// Hardcoded here because it's a frozen reference distribution the UI
// uses purely for visual grounding — not for anything predictive. If
// the stats file ever changes, these numbers should change with it.
const MARKET = {
  q1: 129000,
  median: 160000,
  q3: 213000,
  // Axis range: clip the long tail so the interquartile band isn't a
  // thin sliver. 95th-percentile-ish window for readability.
  axisMin: 60000,
  axisMax: 420000,
}

// Test-set RMSE from Step 3 (random forest winner). Used as a
// plain-English ±uncertainty band under the point estimate. It's a
// conservative read — the true CI is tighter — but it's honest.
const RMSE = 25650

// Clamp + project a price into a 0..1 position along the axis range.
function positionOf(price) {
  const clamped = Math.max(MARKET.axisMin, Math.min(MARKET.axisMax, price))
  return (clamped - MARKET.axisMin) / (MARKET.axisMax - MARKET.axisMin)
}

// Where the prediction lands relative to the training distribution —
// used for a one-line qualitative caption under the chart.
function bandLabel(price) {
  if (price < MARKET.q1) return 'below the training-set interquartile range'
  if (price > MARKET.q3) return 'above the training-set interquartile range'
  return 'inside the training-set interquartile range'
}

// Horizontal market-range sparkline. The full bar is the axis; a
// shaded rectangle marks the interquartile band; a hairline marks the
// median; a terracotta pin drops in for the prediction with a soft
// confidence band (±RMSE) swept in underneath.
function MarketRange({ price, inView }) {
  const { q1Pos, q3Pos, medianPos, pricePos, lowPos, highPos } = useMemo(() => {
    return {
      q1Pos: positionOf(MARKET.q1),
      q3Pos: positionOf(MARKET.q3),
      medianPos: positionOf(MARKET.median),
      pricePos: positionOf(price),
      lowPos: positionOf(price - RMSE),
      highPos: positionOf(price + RMSE),
    }
  }, [price])

  return (
    <div className="relative mx-auto mt-20 max-w-3xl">
      <div className="flex items-baseline justify-between text-[11px] uppercase tracking-eyebrow text-muted">
        <span>Where it sits vs. the market</span>
        <span className="font-mono tabular">
          ±{formatPrice(RMSE)} (test RMSE)
        </span>
      </div>

      <div className="relative mt-5 h-[72px]">
        {/* Axis rail */}
        <div className="absolute left-0 right-0 top-1/2 h-[2px] -translate-y-1/2 rounded-full bg-seam/70" />

        {/* Interquartile band: draws itself from left to right */}
        <motion.div
          initial={{ scaleX: 0, opacity: 0 }}
          animate={inView ? { scaleX: 1, opacity: 1 } : {}}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
          style={{
            left: `${q1Pos * 100}%`,
            right: `${(1 - q3Pos) * 100}%`,
            transformOrigin: 'left',
          }}
          className="absolute top-1/2 h-3 -translate-y-1/2 rounded-full bg-brass/25"
        />

        {/* Median tick */}
        <motion.div
          initial={{ opacity: 0, scaleY: 0 }}
          animate={inView ? { opacity: 1, scaleY: 1 } : {}}
          transition={{ duration: 0.5, delay: 0.9 }}
          style={{ left: `${medianPos * 100}%` }}
          className="absolute top-1/2 h-6 w-px -translate-x-1/2 -translate-y-1/2 bg-brass"
        />
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ duration: 0.5, delay: 1 }}
          style={{ left: `${medianPos * 100}%` }}
          className="absolute top-[calc(50%+18px)] -translate-x-1/2 whitespace-nowrap font-mono text-[10px] uppercase tracking-eyebrow text-muted"
        >
          median · {formatPrice(MARKET.median)}
        </motion.div>

        {/* Confidence band under the prediction */}
        <motion.div
          initial={{ scaleX: 0, opacity: 0 }}
          animate={inView ? { scaleX: 1, opacity: 1 } : {}}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay: 1.4 }}
          style={{
            left: `${lowPos * 100}%`,
            right: `${(1 - highPos) * 100}%`,
            transformOrigin: 'center',
          }}
          className="absolute top-1/2 h-[18px] -translate-y-1/2 rounded-full bg-terracotta/20"
        />

        {/* Prediction pin */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: 1.7 }}
          style={{ left: `${pricePos * 100}%` }}
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
        >
          <span className="relative block h-4 w-4 rounded-full bg-terracotta shadow-cta ring-4 ring-canvas">
            <motion.span
              className="absolute inset-0 rounded-full bg-terracotta/50"
              animate={{ scale: [1, 2, 1], opacity: [0.7, 0, 0.7] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: 'easeOut' }}
            />
          </span>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ duration: 0.5, delay: 1.9 }}
          style={{ left: `${pricePos * 100}%` }}
          className="absolute top-[calc(50%-30px)] -translate-x-1/2 whitespace-nowrap font-mono text-[10px] uppercase tracking-eyebrow text-terracotta"
        >
          prediction
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={inView ? { opacity: 1 } : {}}
        transition={{ duration: 0.6, delay: 2.1 }}
        className="mt-14 text-center text-sm text-muted"
      >
        This estimate sits {bandLabel(price)}.
      </motion.div>
    </div>
  )
}

export default function PriceReveal({ price, modelName }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-160px' })
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    if (!inView || price == null) return
    const duration = 1800
    const start = performance.now()
    let raf
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1)
      setDisplay(Math.round(price * easeOutCubic(t)))
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [inView, price])

  return (
    <section ref={ref} className="mx-auto max-w-6xl px-6 pb-32">
      <SectionHeading step="03" eyebrow="Estimate" title="The model's best guess" />

      <div className="relative mt-16">
        {/* Soft radial aura behind the number — purely atmospheric, gives
            the price a weightless "lit from behind" feel on the aurora. */}
        <motion.div
          aria-hidden
          initial={{ opacity: 0, scale: 0.8 }}
          animate={inView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 1.8, ease: [0.22, 1, 0.36, 1] }}
          className="pointer-events-none absolute inset-x-0 top-1/2 mx-auto h-[460px] max-w-4xl -translate-y-1/2 rounded-full blur-3xl"
          style={{
            background:
              'radial-gradient(circle, rgba(194,125,92,0.18) 0%, rgba(183,154,107,0.12) 45%, transparent 70%)',
          }}
        />

        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8 }}
          className="relative text-center text-[11px] uppercase tracking-eyebrow text-muted"
        >
          Predicted sale price
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40, letterSpacing: '-0.02em' }}
          animate={inView ? { opacity: 1, y: 0, letterSpacing: '-0.03em' } : {}}
          transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
          className="relative mt-4 text-center font-display font-light leading-[0.88] text-ink tabular"
          style={{ fontSize: 'clamp(4rem, 18vw, 15rem)' }}
        >
          {formatPrice(display)}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 1.2, duration: 0.8 }}
          className="relative mt-8 flex items-center justify-center gap-4 text-[11px] uppercase tracking-eyebrow text-muted"
        >
          <span className="inline-block h-px w-10 bg-brass" />
          <span>Point estimate · {modelName ?? 'trained regressor'}</span>
          <span className="inline-block h-px w-10 bg-brass" />
        </motion.div>

        <MarketRange price={price} inView={inView} />
      </div>
    </section>
  )
}
