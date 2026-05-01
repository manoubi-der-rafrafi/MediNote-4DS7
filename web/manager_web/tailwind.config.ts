import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#FBF5EC',
        card: '#ffffff',
        ink: '#1F1F1D',
        mute: '#6B6B66',
        line: '#E5E4DE',
        brand: '#BA7517',
        'brand-dark': '#633806',
        'brand-soft': '#FAEEDA',
        ok: '#1D9E75',
        warn: '#BA7517',
        bad: '#B8263E',
        info: '#378ADD',
        purple: '#7F77DD',
      },
      fontSize: {
        11: '11px',
        13: '13px',
        22: '22px',
        24: '24px',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', "'SF Pro Display'", 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config

