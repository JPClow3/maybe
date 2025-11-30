/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Enable dark mode with class strategy
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
        // Semantic color tokens - Purple/Violet primary for depth
        primary: {
          DEFAULT: '#7c3aed', // Violet 600
          hover: '#6d28d9', // Violet 700
          light: '#a78bfa', // Violet 400
          dark: '#5b21b6', // Violet 800
          50: '#ede9fe', // Violet 50
          100: '#ddd6fe', // Violet 100
          200: '#c4b5fd', // Violet 200
          300: '#a78bfa', // Violet 300
          400: '#8b5cf6', // Violet 400
          500: '#7c3aed', // Violet 500
          600: '#7c3aed', // Violet 600 (primary)
          700: '#6d28d9', // Violet 700
          800: '#5b21b6', // Violet 800
          900: '#4c1d95', // Violet 900
        },
        violet: {
          50: '#ede9fe',
          100: '#ddd6fe',
          200: '#c4b5fd',
          300: '#a78bfa',
          400: '#8b5cf6',
          500: '#7c3aed',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
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
        // Glass surface colors (from Phase 0)
        glass: {
          // Dark mode
          dark: {
            primary: 'rgba(0, 0, 0, 0.4)',
            secondary: 'rgba(0, 0, 0, 0.3)',
            header: 'rgba(0, 0, 0, 0.5)',
            mobile: 'rgba(0, 0, 0, 0.95)',
            border: 'rgba(255, 255, 255, 0.1)',
            borderSecondary: 'rgba(255, 255, 255, 0.08)',
            borderHeader: 'rgba(255, 255, 255, 0.12)',
          },
          // Light mode
          light: {
            primary: 'rgba(255, 255, 255, 0.7)',
            secondary: 'rgba(255, 255, 255, 0.6)',
            mobile: 'rgba(255, 255, 255, 0.95)',
            border: 'rgba(0, 0, 0, 0.1)',
            borderSecondary: 'rgba(0, 0, 0, 0.08)',
          },
        },
        // Ambient orb colors (subtle, not neon) - Added purple
        orb: {
          emerald: 'rgba(16, 185, 129, 0.15)',
          indigo: 'rgba(99, 102, 241, 0.15)',
          rose: 'rgba(244, 63, 94, 0.15)',
          violet: 'rgba(124, 58, 237, 0.15)',
        },
      },
      boxShadow: {
        // Custom shadows for glass effect
        'float': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'highlight': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
        'glow-emerald': '0 0 12px rgba(16, 185, 129, 0.2)',
        'glow-indigo': '0 0 12px rgba(99, 102, 241, 0.2)',
        'glow-rose': '0 0 12px rgba(244, 63, 94, 0.2)',
        'glow-violet': '0 0 12px rgba(124, 58, 237, 0.2)',
        'glow-violet-strong': '0 0 16px rgba(124, 58, 237, 0.3)',
      },
      backgroundImage: {
        // Mesh gradient utilities
        'mesh-emerald': 'radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.1) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.1) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(244, 63, 94, 0.1) 0px, transparent 50%), radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%)',
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

