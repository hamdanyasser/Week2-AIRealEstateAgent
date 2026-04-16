import { motion } from 'framer-motion'

// Editorial section heading: numbered eyebrow, serif title, optional blurb.
// Reused by every result movement so the page reads like a printed page.
export default function SectionHeading({ step, eyebrow, title, blurb }) {
  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-120px' }}
        transition={{ duration: 0.7 }}
        className="flex items-center gap-4 text-[11px] uppercase tracking-eyebrow text-muted"
      >
        <span className="font-mono text-terracotta">{step}</span>
        <span className="inline-block h-px w-10 bg-brass" />
        <span>{eyebrow}</span>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-120px' }}
        transition={{ duration: 0.8, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        className="mt-5 font-display text-4xl md:text-6xl tracking-tight leading-[1.02] max-w-3xl"
      >
        {title}
      </motion.h2>

      {blurb && (
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-120px' }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-6 text-muted text-base md:text-lg max-w-2xl leading-relaxed"
        >
          {blurb}
        </motion.p>
      )}
    </div>
  )
}
