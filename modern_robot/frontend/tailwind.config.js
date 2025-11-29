/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        robot: {
          dark: '#1a1a1a',
          panel: '#2a2a2a',
          accent: '#00ff88',
          danger: '#ff4444',
          warning: '#ffbb00'
        }
      }
    },
  },
  plugins: [],
}




