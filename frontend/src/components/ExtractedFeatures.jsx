import { motion } from 'framer-motion'
import { FEATURE_META, FEATURE_ORDER } from '../lib/featureMeta.js'
import { formatNumber } from '../lib/format.js'
import SectionHeading from './SectionHeading.jsx'

export default function ExtractedFeatures({
  features,
  missing,
  mode = 'result',
}) {
  const missingSet = new Set(missing ?? [])
  const isReviewMode = mode === 'review'

  return (
    <section className="mx-auto max-w-6xl px-6 pb-28">
      <SectionHeading
        step="01"
        eyebrow="Signal"
        title={
          isReviewMode
            ? 'What the assistant extracted'
            : 'What the assistant understood'
        }
        blurb={
          isReviewMode
            ? "Stage 1 has translated your description into the twelve features the model expects. Blank cards need your review before we run the estimate."
            : "Stage 1 maps your free-text description onto the twelve features the model was trained on. Fields the description left out appear faded - those are filled by the pipeline's own imputer before prediction."
        }
      />

      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-120px' }}
        variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
        className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-seam bg-seam shadow-lift sm:grid-cols-2 lg:grid-cols-3"
      >
        {FEATURE_ORDER.map((key) => {
          const meta = FEATURE_META[key]
          const value = features?.[key]
          const isMissing = missingSet.has(key) || value == null || value === ''

          return (
            <motion.div
              key={key}
              variants={{
                hidden: { opacity: 0, y: 12 },
                visible: { opacity: 1, y: 0 },
              }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className={`group relative flex min-h-[140px] flex-col justify-between bg-canvas p-7 md:p-8 ${
                isMissing ? 'opacity-60' : ''
              }`}
            >
              <div className="text-[10px] uppercase tracking-eyebrow text-muted">
                {meta.label}
              </div>

              <div className="mt-6 font-display text-3xl leading-none text-ink tabular md:text-4xl">
                {isMissing ? (
                  <span className="font-light italic text-muted">-</span>
                ) : meta.scale ? (
                  <span>
                    {value}
                    <span className="text-xl font-light text-muted/80">
                      {' '}
                      / {meta.scale}
                    </span>
                  </span>
                ) : (
                  <span>{formatNumber(value, meta.unit) ?? value}</span>
                )}
              </div>

              {isMissing && (
                <div className="mt-4 text-[10px] uppercase tracking-eyebrow text-terracotta">
                  {isReviewMode ? 'Needs your review' : 'Inferred from training data'}
                </div>
              )}
            </motion.div>
          )
        })}
      </motion.div>
    </section>
  )
}
