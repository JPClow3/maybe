/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // 1. Busca nos templates globais na raiz
    './templates/**/*.html',
    
    // 2. Busca dentro de cada app (ex: finance/templates/finance/...)
    './**/templates/**/*.html',
    
    // 3. Se você usar classes no Python (forms.py, views.py)
    './**/*.py',
    
    // 4. Se usar Javascript vanilla
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Semantic color tokens for Brazilian minimalism
        primary: {
          DEFAULT: '#18181b', // Zinc 900
          hover: '#27272a', // Zinc 800
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
        },
        surface: {
          DEFAULT: '#ffffff',
          subtle: '#f9fafb', // Gray 50
        },
        money: {
          income: '#059669', // Emerald 600
          expense: '#18181b', // Zinc 900 (gray instead of red)
          debt: '#e11d48', // Rose 600 (only for critical alerts)
        },
        // Keep existing color scales for backward compatibility
        secondary: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      fontFamily: {
        sans: ['Geist Sans', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}

