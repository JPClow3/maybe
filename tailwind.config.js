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
        // The Void (Backgrounds) - Luma Design System
        singularity: '#000000', // The deepest layer (body background)
        deepSpace: '#050505', // The primary app canvas
        matter: '#121212', // Solid cards (fallback/modal)
        
        // Bioluminescence (Brand & Accents) - Luma Design System
        electricIndigo: '#6366f1', // Primary Brand (indigo-500)
        deepViolet: '#7c3aed', // Secondary gradient stop (violet-600)
        neonFuchsia: '#ec4899', // Accent (fuchsia-500)
        cyberCyan: '#06b6d4', // Accent (cyan-500) - Luma spec
        
        // Primary color system - Electric Indigo as primary brand
        primary: {
          DEFAULT: '#6366f1', // Electric Indigo
          hover: '#4f46e5', // indigo-600
          light: '#818cf8', // indigo-400
          dark: '#4f46e5', // indigo-600
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1', // Electric Indigo (primary)
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        
        // Violet for secondary gradients
        violet: {
          50: '#ede9fe',
          100: '#ddd6fe',
          200: '#c4b5fd',
          300: '#a78bfa',
          400: '#8b5cf6',
          500: '#7c3aed',
          600: '#7c3aed', // Deep Violet
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
        
        // Glass surface colors - Luma Design System
        glass: {
          base: 'rgba(18, 18, 18, 0.4)', // Standard panels/cards - Luma spec
          highlight: 'rgba(255, 255, 255, 0.05)', // Hover states, active items - Luma spec
          // Dark mode
          dark: {
            primary: 'rgba(18, 18, 18, 0.4)', // Luma spec
            secondary: 'rgba(18, 18, 18, 0.3)',
            header: 'rgba(18, 18, 18, 0.5)',
            mobile: 'rgba(18, 18, 18, 0.95)',
            border: 'rgba(255, 255, 255, 0.05)',
            borderSecondary: 'rgba(255, 255, 255, 0.03)',
            borderHeader: 'rgba(255, 255, 255, 0.08)',
          },
          // Light mode (fallback)
          light: {
            primary: 'rgba(255, 255, 255, 0.7)',
            secondary: 'rgba(255, 255, 255, 0.6)',
            mobile: 'rgba(255, 255, 255, 0.95)',
            border: 'rgba(0, 0, 0, 0.1)',
            borderSecondary: 'rgba(0, 0, 0, 0.08)',
          },
        },
        
        // Semantic Data (The HUD) - Luma Design System
        // These are used strictly for financial data
        emerald: {
          400: '#34d399',
          500: '#10b981', // Asset / Gain - Luma spec
        },
        rose: {
          400: '#f43f5e', // Liability / Loss - Luma spec
          500: '#f43f5e', // Luma spec
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4', // Cyber Cyan - Luma spec
        },
        amber: {
          400: '#fbbf24', // Warning - Luma spec
        },
        orange: {
          400: '#f97316', // Crypto / Volatile - Luma spec
        },
        slate: {
          400: '#94a3b8', // Neutral / Info
        },
        
        // Legacy colors (for backward compatibility)
        surface: {
          DEFAULT: '#ffffff',
          subtle: '#f9fafb', // Gray 50
        },
        money: {
          income: '#10b981', // Emerald 500 - Asset/Gain - Luma spec
          expense: '#f43f5e', // Rose 400 - Liability/Loss - Luma spec
          debt: '#f43f5e', // Rose 400 - Luma spec
          crypto: '#f97316', // Orange 400 - Crypto/Volatile - Luma spec
        },
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
        // Ambient orb colors (subtle, not neon) - Luma Design System
        orb: {
          emerald: 'rgba(16, 185, 129, 0.15)', // Luma emerald-500
          indigo: 'rgba(99, 102, 241, 0.15)',
          rose: 'rgba(244, 63, 94, 0.15)',
          violet: 'rgba(124, 58, 237, 0.15)',
          fuchsia: 'rgba(236, 72, 153, 0.15)',
          cyan: 'rgba(6, 182, 212, 0.15)', // Luma cyan-500 (Cyber Cyan)
          orange: 'rgba(249, 115, 22, 0.15)', // Luma orange-400 (Crypto/Volatile)
        },
      },
      boxShadow: {
        // Luma Design System shadows
        'glow': '0 0 20px rgba(99, 102, 241, 0.3)', // Primary Brand glow - Luma spec
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.36)', // Glass panel shadow
        // Legacy shadows (for backward compatibility)
        'float': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'highlight': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
        'glow-emerald': '0 0 12px rgba(16, 185, 129, 0.2)', // Luma emerald-500 (Asset/Gain)
        'glow-indigo': '0 0 12px rgba(99, 102, 241, 0.2)',
        'glow-rose': '0 0 12px rgba(244, 63, 94, 0.2)',
        'glow-violet': '0 0 20px rgba(124, 58, 237, 0.3)', // Secondary Brand glow - Luma spec
        'glow-violet-strong': '0 0 16px rgba(124, 58, 237, 0.3)',
        'glow-cyan': '0 0 15px rgba(6, 182, 212, 0.4)', // Cyber Cyan glow - Luma spec
        'glow-orange': '0 0 15px rgba(249, 115, 22, 0.4)', // Crypto/Volatile glow - Luma spec
      },
      backgroundImage: {
        // Mesh gradient utilities
        'mesh-emerald': 'radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.1) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.1) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(244, 63, 94, 0.1) 0px, transparent 50%), radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%)', // Luma emerald-500
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      fontFamily: {
        sans: ['Inter', 'Geist Sans', 'system-ui', 'sans-serif'], // Interface font
        mono: ['JetBrains Mono', 'Geist Mono', 'monospace'], // Data font
      },
      animation: {
        'blob': 'blob 7s infinite',
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
      },
      keyframes: {
        blob: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -50px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.9)' },
          '100%': { transform: 'translate(0px, 0px) scale(1)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
