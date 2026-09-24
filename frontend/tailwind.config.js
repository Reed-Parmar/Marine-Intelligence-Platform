/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        marine: {
          950: '#050B14',
          900: '#0A1224',
          850: '#0F1A34',
          800: '#152449',
          750: '#1C2F5D',
          700: '#233B73',
          600: '#31529E',
          500: '#4370D4',
        },
        ocean: {
          cyan: '#00F0FF',
          teal: '#06D6A0',
          blue: '#1E88E5',
          amber: '#FFB703',
          coral: '#FF4D6D',
          violet: '#7928CA',
        },
        surface: {
          dark: 'rgba(10, 18, 36, 0.85)',
          card: 'rgba(15, 26, 52, 0.75)',
          border: 'rgba(49, 82, 158, 0.35)',
          hover: 'rgba(35, 59, 115, 0.5)',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -5px rgba(0, 240, 255, 0.35)',
        'glow-teal': '0 0 20px -5px rgba(6, 214, 160, 0.35)',
        'glow-card': '0 10px 30px -10px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
