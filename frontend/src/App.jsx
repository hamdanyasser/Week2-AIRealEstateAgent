import { useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

import Hero from './components/Hero.jsx'
import QueryComposer from './components/QueryComposer.jsx'
import ThinkingSequence from './components/ThinkingSequence.jsx'
import ExtractedFeatures from './components/ExtractedFeatures.jsx'
import FeatureReview from './components/FeatureReview.jsx'
import MissingFeatures from './components/MissingFeatures.jsx'
import PriceReveal from './components/PriceReveal.jsx'
import Explanation from './components/Explanation.jsx'
import ErrorState from './components/ErrorState.jsx'
import Footer from './components/Footer.jsx'
import { analyzeProperty, extractProperty } from './lib/api.js'

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// App is the single source of truth for the UI state machine:
//   idle       -> hero + composer
//   extracting -> Stage 1 thinking
//   review     -> extracted features + review/fill step
//   predicting -> full pipeline thinking
//   result     -> final price + interpretation
//   error      -> friendly recovery state
export default function App() {
  const [status, setStatus] = useState('idle')
  const [query, setQuery] = useState('')
  const [extraction, setExtraction] = useState(null)
  const [reviewedFeatures, setReviewedFeatures] = useState(null)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const reviewRef = useRef(null)
  const resultsRef = useRef(null)

  // Freeze the missing-field list at extract-time. If we re-derived it
  // from `reviewedFeatures` on every render, typing a value would make
  // the field non-missing and unmount its own input mid-edit.
  const reviewMissing = extraction?.missing_features ?? []

  async function handleAnalyze(text) {
    setQuery(text)
    setStatus('extracting')
    setError(null)
    setData(null)
    setExtraction(null)
    setReviewedFeatures(null)

    try {
      const [result] = await Promise.all([
        extractProperty(text),
        delay(1200),
      ])

      setExtraction(result)
      setReviewedFeatures(result.extracted_features)
      setStatus('review')

      setTimeout(() => {
        reviewRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 120)
    } catch (err) {
      setError(err)
      setStatus('error')
    }
  }

  async function handlePredict() {
    if (!query || !reviewedFeatures) return

    setStatus('predicting')
    setError(null)
    setData(null)

    try {
      const [result] = await Promise.all([
        analyzeProperty(query, 'v2', reviewedFeatures),
        delay(2000),
      ])

      setData(result)
      setStatus('result')

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 120)
    } catch (err) {
      setError(err)
      setStatus('error')
    }
  }

  function handleFeatureChange(key, value) {
    setReviewedFeatures((current) => ({
      ...(current ?? {}),
      [key]: value,
    }))
  }

  function handleReset() {
    setStatus('idle')
    setQuery('')
    setExtraction(null)
    setReviewedFeatures(null)
    setData(null)
    setError(null)
  }

  const isBusy = status === 'extracting' || status === 'predicting'

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-canvas text-ink">
      <div className="aurora fixed inset-0 z-0" aria-hidden>
        <div className="aurora-orb aurora-a" />
        <div className="aurora-orb aurora-b" />
        <div className="aurora-orb aurora-c" />
      </div>
      <div className="grain fixed inset-0 z-0" aria-hidden />

      <main className="relative z-10">
        <Hero />

        <QueryComposer
          onAnalyze={handleAnalyze}
          disabled={isBusy}
          initialValue={query}
        />

        <AnimatePresence mode="wait">
          {status === 'extracting' && (
            <motion.div
              key="extracting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
            >
              <ThinkingSequence mode="extract" />
            </motion.div>
          )}

          {status === 'review' && extraction && reviewedFeatures && (
            <motion.div
              key="review"
              ref={reviewRef}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
            >
              <ExtractedFeatures
                features={reviewedFeatures}
                missing={reviewMissing}
                mode="review"
              />
              <FeatureReview
                features={reviewedFeatures}
                missing={reviewMissing}
                onChange={handleFeatureChange}
                onPredict={handlePredict}
                disabled={false}
              />
            </motion.div>
          )}

          {status === 'predicting' && (
            <motion.div
              key="predicting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
            >
              <ThinkingSequence mode="full" />
            </motion.div>
          )}

          {status === 'error' && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
            >
              <ErrorState error={error} onRetry={handleReset} />
            </motion.div>
          )}

          {status === 'result' && data && (
            <motion.div
              key="result"
              ref={resultsRef}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6 }}
            >
              <ExtractedFeatures
                features={data.extracted_features}
                missing={data.missing_features}
              />
              <MissingFeatures missing={data.missing_features} />
              <PriceReveal
                price={data.predicted_price}
                modelName={data.model_name}
              />
              <Explanation
                interpretation={data.interpretation}
                onReset={handleReset}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <Footer />
      </main>
    </div>
  )
}
