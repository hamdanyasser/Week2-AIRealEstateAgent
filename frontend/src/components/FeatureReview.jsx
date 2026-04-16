import { motion } from 'framer-motion'
import { FEATURE_META } from '../lib/featureMeta.js'
import SectionHeading from './SectionHeading.jsx'

const TOTAL_FEATURES = 12

function parseValue(key, rawValue) {
  const meta = FEATURE_META[key]
  if (rawValue === '') return null
  if (meta?.input !== 'number') return rawValue

  const parsed =
    meta.valueType === 'int'
      ? Number.parseInt(rawValue, 10)
      : Number.parseFloat(rawValue)

  return Number.isNaN(parsed) ? null : parsed
}

export default function FeatureReview({
  features,
  missing,
  onChange,
  onPredict,
  disabled,
}) {
  const missingKeys = Array.isArray(missing) ? missing : []
  const capturedCount = TOTAL_FEATURES - missingKeys.length

  return (
    <section className="mx-auto max-w-6xl px-6 pb-28">
      <SectionHeading
        step="Review"
        eyebrow="Before the model runs"
        title="Confirm the details we will price"
        blurb="Stage 1 has mapped your description onto the model's 12 features. Fill anything important that was left blank, then run the estimate from this reviewed feature set."
      />

      <div className="mt-14 grid gap-6 md:grid-cols-2">
        <div className="rounded-[24px] border border-seam bg-surface p-8 shadow-lift">
          <div className="text-[11px] uppercase tracking-eyebrow text-muted">
            Coverage
          </div>
          <div className="mt-4 font-display text-5xl text-ink">
            {capturedCount}/{TOTAL_FEATURES}
          </div>
          <p className="mt-4 max-w-md text-sm leading-6 text-muted">
            The extractor already found {capturedCount} feature
            {capturedCount === 1 ? '' : 's'} from your description.
          </p>
        </div>

        <div className="rounded-[24px] border border-seam bg-canvas p-8 shadow-lift">
          <div className="text-[11px] uppercase tracking-eyebrow text-muted">
            Missing fields
          </div>
          <div className="mt-4 font-display text-5xl text-ink">
            {missingKeys.length}
          </div>
          <p className="mt-4 max-w-md text-sm leading-6 text-muted">
            Leave a field blank if you genuinely do not know it. The
            model will fall back to training-set medians and modes for
            anything you keep empty.
          </p>
        </div>
      </div>

      {missingKeys.length > 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-120px' }}
          transition={{ duration: 0.5 }}
          className="mt-10 grid gap-5 md:grid-cols-2"
        >
          {missingKeys.map((key) => {
            const meta = FEATURE_META[key] ?? {}
            const value = features?.[key] ?? ''
            return (
              <label
                key={key}
                className="rounded-[22px] border border-seam bg-surface p-6 shadow-lift"
              >
                <span className="block text-[11px] uppercase tracking-eyebrow text-muted">
                  {meta.label ?? key}
                </span>

                <input
                  type={meta.input === 'number' ? 'number' : 'text'}
                  min={meta.min}
                  max={meta.max}
                  step={meta.step}
                  value={value}
                  disabled={disabled}
                  onChange={(event) =>
                    onChange(key, parseValue(key, event.target.value))
                  }
                  placeholder={meta.placeholder ?? ''}
                  className="mt-4 w-full bg-transparent border-b border-seam pb-3 font-display text-3xl text-ink placeholder:text-muted/45 outline-none disabled:opacity-60"
                />

                <span className="mt-3 block text-sm leading-6 text-muted">
                  {meta.helper ??
                    (meta.unit ? `Expected unit: ${meta.unit}.` : 'Optional field.')}
                </span>
              </label>
            )
          })}
        </motion.div>
      ) : (
        <div className="mt-10 rounded-[24px] border border-seam bg-surface p-8 shadow-lift text-muted">
          Nothing is missing. You can run the price estimate immediately.
        </div>
      )}

      <div className="mt-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <p className="max-w-2xl text-sm leading-6 text-muted">
          The prediction uses exactly these reviewed values. Any field
          still left blank will be imputed by the trained sklearn
          pipeline before the estimate is generated.
        </p>

        <button
          type="button"
          onClick={onPredict}
          disabled={disabled}
          className="inline-flex items-center justify-center gap-3 rounded-full bg-terracotta px-7 py-4 text-[11px] uppercase tracking-eyebrow text-canvas shadow-cta transition-colors hover:bg-[#b26b49] disabled:opacity-40 disabled:shadow-none"
        >
          {disabled ? 'Preparing estimate...' : 'Run the prediction'}
        </button>
      </div>
    </section>
  )
}
