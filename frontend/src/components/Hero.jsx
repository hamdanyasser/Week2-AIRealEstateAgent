import { motion } from 'framer-motion'

const EASE = [0.22, 1, 0.36, 1]

export default function Hero() {
  return (
    <header className="relative mx-auto max-w-6xl px-6 pt-20 md:pt-28 pb-10">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: EASE }}
        className="flex items-center gap-3 text-[11px] uppercase tracking-eyebrow text-muted"
      >
        <span className="inline-block h-px w-8 bg-brass" />
        Ames Intelligence · Housing Price Studio
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.0, delay: 0.1, ease: EASE }}
        className="mt-6 font-display font-light text-[clamp(2.75rem,8vw,7.5rem)] leading-[0.92] tracking-tight"
      >
        Describe a home.
        <br />
        <span className="italic text-terracotta font-normal">
          We&apos;ll read between the lines.
        </span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.5 }}
        className="mt-8 max-w-2xl text-lg md:text-xl text-muted leading-relaxed"
      >
        A natural-language studio for the Ames Housing dataset. A language
        model reads your description, a trained regressor turns it into a
        number, and a second pass explains the result in plain English —
        grounded in the same 2,051 homes the model learned from.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.8 }}
        className="mt-12 flex flex-wrap items-baseline gap-x-10 gap-y-4 text-[11px] uppercase tracking-eyebrow text-muted"
      >
        <Stat value="2,051" label="Training rows" />
        <Stat value="$25,652" label="Test RMSE" />
        <Stat value="0.896" label="Held-out R²" />
        <Stat value="FastAPI · sklearn · GPT-4o" label="Stack" />
      </motion.div>
    </header>
  )
}

function Stat({ value, label }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-ink font-mono text-[13px] tracking-normal tabular">
        {value}
      </span>
      <span>{label}</span>
    </div>
  )
}
