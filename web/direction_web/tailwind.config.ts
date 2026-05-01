import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0E0E10',
        s1: '#18181C',
        s2: '#22222A',
        s3: '#2A2A35',
        bd: 'rgba(255,255,255,0.08)',
        manager: {
          DEFAULT: '#A78BFA',
          bg: 'rgba(167,139,250,0.12)',
        },
        marketing: {
          DEFAULT: '#FB923C',
          bg: 'rgba(251,146,60,0.12)',
        },
        direction: {
          DEFAULT: '#F87171',
          bg: 'rgba(248,113,113,0.12)',
        },
        blue: '#4F8EF7',
        teal: '#2DD4BF',
        green: '#34D399',
        orange: '#FB923C',
        red: '#F87171',
        gold: '#FBBF24',
        purple: '#A78BFA',
      },
      backgroundColor: {
        base: '#0E0E10',
        card: '#18181C',
      },
    },
  },
  plugins: [],
} satisfies Config
