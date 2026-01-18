/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#FFC700', // Nova Yellow
          secondary: '#000000', // Ink Black
          background: '#F4F4F3', // Neutral
          surface: '#FFFFFF',
          text: '#000000',
          muted: '#666666',
          border: '#E5E5E5',
          blue: '#3B52FF', // Electric Blue
          'blue-light': '#5A6FFF',
          'blue-dark': '#2A3FCC',
          aqua: '#00FFC7', // Ion Aqua
          'aqua-light': '#33FFD4',
          'aqua-dark': '#00CC9F',
          orange: '#EA5300', // Burnt Orange
          'orange-light': '#FF6B1A',
          'orange-dark': '#C44500',
        }
      },
      fontFamily: {
        'heading-major': ['Noto Serif Condensed', 'serif'],
        'heading-minor': ['Noto Serif', 'serif'],
        heading: ['Noto Serif Condensed', 'serif'],
        body: ['Noto Sans', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '0.75rem',
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.06)',
        button: '0 1px 2px 0 rgb(255 199 0 / 0.3), 0 1px 3px 0 rgb(255 199 0 / 0.15)',
      },
    }
  },
  plugins: [],
};
