/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#F6F5F0',
        card: '#ffffff',
        ink: '#1F1F1D',
        mute: '#6B6B66',
        line: '#E5E4DE',
        ok: '#1D9E75',
        warn: '#BA7517',
        bad: '#B8263E',
        info: '#378ADD',
        purple: '#7F77DD',
        'sidebar-bg': '#2C2C2A',
      },
      fontSize: {
        xs: ['11px', '1.4'],
        sm: ['13px', '1.5'],
        base: ['13px', '1.5'],
        lg: ['22px', '1.3'],
        xl: ['24px', '1.2'],
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"', '"Inter"', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '17': '1.75rem',
      },
    },
  },
  plugins: [],
}
