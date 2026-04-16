import { motion } from 'framer-motion'
import { FEATURE_META } from '../lib/featureMeta.js'
import SectionHeading from './SectionHeading.jsx'

export default function MissingFeatures({ missing }) {
  const hasMissing = Array.isArray(missing) && missing.length > 0

  return (
    <section className="mx-auto max-w-6xl px-6 pb-28">
      {hasMissing ? (
        <>
          <SectionHeading
            step="02"
            eyebrow="Assumptions"
            title="What we had to infer"
            blurb="These fields were still blank when the prediction ran. Rather than guess, the pipeline filled them with the same medians and modes it learned from the training set - so the estimate stays honest about what came from you and what came from fallback defaults."
          />

          <motion.ul
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-120px' }}
            variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
            className="mt-14 border-t border-seam"
          >
            {missing.map((key) => {
              const meta = FEATURE_META[key]
              return (
                <motion.li
                  key={key}
                  variants={{
                    hidden: { opacity: 0, x: -12 },
                    visible: { opacity: 1, x: 0 },
                  }}
                  transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                  className="flex items-center gap-6 border-b border-seam py-6"
                >
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-brass" />
                  <span className="font-display text-2xl text-ink md:text-3xl">
                    {meta?.label ?? key}
                  </span>
                  <span className="ml-auto text-right text-[11px] uppercase tracking-eyebrow text-muted">
                    imputed at prediction time
                  </span>
                </motion.li>
              )
            })}
          </motion.ul>
        </>
      ) : (
        <SectionHeading
          step="02"
          eyebrow="Assumptions"
          title="Nothing left to infer."
          blurb="Your reviewed feature set covered every field the model was trained on, so the estimate below uses only values the user confirmed."
        />
      )}
    </section>
  )
}
