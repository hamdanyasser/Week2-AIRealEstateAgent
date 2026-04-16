import { motion } from 'framer-motion'
import { RotateCcw } from 'lucide-react'
import SectionHeading from './SectionHeading.jsx'

export default function Explanation({ interpretation, onReset }) {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-32">
      <SectionHeading
        step="04"
        eyebrow="Reasoning"
        title="Why this number"
        blurb="A second language model pass reads the predicted price alongside the training-set medians and the neighborhood average, then explains the result in plain English — grounded in the exact distribution the model learned from."
      />

      <motion.blockquote
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-140px' }}
        transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        className="mt-14 relative rounded-[28px] border border-seam bg-surface p-10 md:p-16 shadow-lift"
      >
        <span
          aria-hidden
          className="absolute -top-8 left-8 md:left-12 font-display text-[8rem] leading-none text-terracotta select-none"
        >
          &ldquo;
        </span>

        <p className="font-display font-light text-2xl md:text-4xl leading-[1.3] text-ink max-w-3xl">
          {interpretation}
        </p>

        <div className="mt-10 flex items-center gap-3 text-[11px] uppercase tracking-eyebrow text-muted">
          <span className="inline-block h-px w-8 bg-brass" />
          Grounded in training-set statistics
        </div>
      </motion.blockquote>

      <div className="mt-14 flex justify-center">
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-3 px-6 py-3.5 rounded-full border border-seam text-ink/80 hover:border-terracotta hover:text-terracotta transition-colors"
        >
          <RotateCcw className="h-4 w-4" />
          <span className="text-[11px] uppercase tracking-eyebrow">
            Try another description
          </span>
        </button>
      </div>
    </section>
  )
}
