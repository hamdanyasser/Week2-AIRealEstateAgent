import { useEffect, useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'
import { formatPrice } from '../lib/format.js'
import SectionHeading from './SectionHeading.jsx'

// Easing: cubic ease-out, so the counter decelerates instead of crawling
// linearly up to the target — reads as deliberate rather than mechanical.
function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
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

      <div className="mt-16 relative">
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8 }}
          className="text-[11px] uppercase tracking-eyebrow text-muted text-center"
        >
          Predicted sale price
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40, letterSpacing: '-0.02em' }}
          animate={inView ? { opacity: 1, y: 0, letterSpacing: '-0.03em' } : {}}
          transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
          className="mt-4 text-center font-display font-light leading-[0.88] text-ink tabular"
          style={{ fontSize: 'clamp(4rem, 18vw, 15rem)' }}
        >
          {formatPrice(display)}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 1.2, duration: 0.8 }}
          className="mt-8 flex items-center justify-center gap-4 text-[11px] uppercase tracking-eyebrow text-muted"
        >
          <span className="inline-block h-px w-10 bg-brass" />
          <span>Point estimate · {modelName ?? 'trained regressor'}</span>
          <span className="inline-block h-px w-10 bg-brass" />
        </motion.div>
      </div>
    </section>
  )
}
