/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f8ff',
          100: '#e0ecff',
          200: '#bdd4ff',
          300: '#8eb3ff',
          400: '#598cff',
          500: '#2f6dff',
          600: '#124df0',
          700: '#0d3bcc',
          800: '#0f31a1',
          900: '#122f80'
        }
      }
    }
  },
  plugins: [],
};
