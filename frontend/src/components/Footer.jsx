export default function Footer() {
  return (
    <footer className="border-t border-seam mt-16">
      <div className="mx-auto max-w-6xl px-6 py-12 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <span className="inline-block h-2 w-2 rounded-full bg-terracotta" />
          <span className="font-display text-xl text-ink">Atelier</span>
          <span className="text-[11px] uppercase tracking-eyebrow text-muted">
            AI Real Estate Intelligence
          </span>
        </div>

        <div className="text-[11px] uppercase tracking-eyebrow text-muted">
          SE Factory · AIE Bootcamp · Week 2
        </div>

        <div className="text-[11px] uppercase tracking-eyebrow text-muted">
          FastAPI · scikit-learn · GPT-4o-mini
        </div>
      </div>
    </footer>
  )
}
