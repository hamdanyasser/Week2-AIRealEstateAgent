/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#F6F1E8',
        surface: '#EFE7DA',
        ink: '#2F3A39',
        muted: '#6B756F',
        teal: '#6E8B83',
        terracotta: '#C27D5C',
        brass: '#B79A6B',
        seam: '#D8CCB8',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      letterSpacing: {
        eyebrow: '0.22em',
      },
      boxShadow: {
        lift: '0 30px 60px -40px rgba(47,58,57,0.35)',
        cta: '0 18px 30px -15px rgba(194,125,92,0.7)',
      },
    },
  },
  plugins: [],
}
