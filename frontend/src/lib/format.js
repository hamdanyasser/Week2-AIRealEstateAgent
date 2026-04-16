export function formatPrice(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatNumber(value, unit) {
  if (value == null) return null
  const n = Number(value)
  if (Number.isNaN(n)) return String(value)
  const pretty = new Intl.NumberFormat('en-US').format(n)
  return unit ? `${pretty} ${unit}` : pretty
}
