# Luma - Personal Finance Application

> **Philosophy**: Finance is energy. It flows, it fluctuates, and it illuminates your life. Luma is not a container for numbers; it is a lens that focuses that energy into a clear signal.

A Django-powered personal finance application optimized for Brazil, built with the **Ethereal Dark Mode** aesthetic. Luma transforms financial data into a clear, beautiful signal emerging from the void.

---

## ✨ The Luma Experience

### The Prism: Visual Identity

Luma derives its name from **luminance**—light, clarity, brightness emerging from the void. In a world of financial noise (darkness), your data is the light. Luma is the lens that focuses it.

**The Logo Concept**: A stylized, abstract prism or lens. A single beam of white light entering and splitting into the constituent colors of your financial life (Assets, Debts, Cash).

### The Physics of Luma

- **Crystalline Glass**: Surfaces are slices of high-density glass floating in a void, with refraction and depth communicated through blur and scale
- **Bioluminescence**: Colors glow with light sources, not flat blocks—indigo, violet, cyan, and fuchsia create an ambient, breathing interface
- **Fluid Motion**: Interactions feel instant (<100ms) with graceful transitions that fade and slide through the medium

---

## 🎨 Visual DNA

### The Void (Surfaces)
- **Singularity** (`#000000`): The deepest layer, body background
- **Deep Space** (`#050505`): The primary app canvas
- **Glass Panels**: Translucent crystalline structures with `backdrop-blur(24px)` that blur backgrounds to provide context

### Bioluminescence (Brand Colors)
- **Electric Indigo** (`#6366f1`): Primary brand—CTAs, active navigation, asset glows
- **Deep Violet** (`#7c3aed`): Secondary gradient stops
- **Neon Fuchsia** (`#ec4899`): Accent sparks and investment highlights
- **Cyber Cyan** (`#06b6d4`): Technology, crypto, future projections

### Semantic Data (The HUD)
- **Assets/Gains**: Emerald (`#10b981`) with text-shadow glow
- **Liabilities/Losses**: Rose (`#f43f5e`) with text-shadow glow
- **Crypto/Volatile**: Orange (`#f97316`) with shadow glow
- **Neutral/Info**: Slate (`#94a3b8`)

### Typography
- **Interface Font**: Inter/Geist Sans for headings, navigation, body copy
- **Data Font**: JetBrains Mono/Geist Mono for currency, percentages, dates—ensuring vertical alignment for faster scanning

---

## 🚀 Features

### Core Functionality
- 💰 **Account Management**: Checking, savings, credit cards, investments, loans, properties, vehicles
- 📊 **Transaction Tracking**: Automatic categorization with intelligent rules engine
- 📈 **Balance Calculation**: Historical tracking with daily balance materialization
- 🎯 **Budget Management**: Category-based budgeting with visual tracking
- 📥 **Import System**: OFX/CSV import for Brazilian banks
- 💳 **Installment Support**: Automatic generation for credit card purchases
- 📉 **B3 Investment Tracking**: Brazilian stock market integration via yfinance
- ⚡ **HTMX Integration**: SPA-like interactions without JavaScript complexity

### Design System
- 🌙 **Ethereal Dark Mode**: Dark-mode first with deep void backgrounds
- 🔮 **Glass Morphism**: Translucent panels with backdrop blur
- ✨ **Ambient Glow**: Bioluminescent accents and semantic color glows
- 🎭 **Spotlight Interactions**: Radial gradients that follow cursor position
- 📱 **Responsive Design**: Mobile-first with fluid layouts

---

## 🛠️ Tech Stack

- **Framework**: Django 5.0+
- **Database**: PostgreSQL 12+
- **Styling**: Tailwind CSS v3.4+ with custom LUMA design system
- **Interactions**: HTMX for SPA-like UI/UX
- **Components**: django-components for reusable UI elements
- **Background Jobs**: Celery + Redis (optional)
- **External APIs**:
  - B3 investment data: yfinance for Brazilian stock market
  - OFX parsing: ofxparse for bank file imports
  - CSV parsing: pandas for data processing

---

## 📋 Requirements

- Python 3.10+
- PostgreSQL 12+
- Redis (for Celery background tasks, optional)
- Node.js (for CSS compilation)

---

## 🚀 Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### 4. Create PostgreSQL Database

```bash
createdb maybe_django
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Build CSS (Required Before First Run)

The LUMA design system is compiled from `static/css/input.css`:

```bash
npm install
npm run css:build
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to see Luma in action.

---

## 📁 Project Structure

```
maybe_django/
├── core/              # User authentication and core models
├── finance/           # Accounts, transactions, balances, categories, rules, budgets
├── investments/       # Securities, holdings, trades, B3 price data
├── imports/           # OFX/CSV file importers
├── templates/         # Django templates with LUMA design system
├── static/
│   ├── css/
│   │   ├── input.css  # LUMA design system source (Tailwind + custom)
│   │   └── main.css   # Compiled CSS (generated)
│   └── js/            # Client-side JavaScript (minimal, HTMX-first)
└── maybe_django/      # Django project settings
```

### Key Directories

- **`finance/services/`**: Business logic services (AccountSyncer, BalanceCalculator, TransferMatcher)
- **`investments/services/`**: B3 price fetching and investment calculations
- **`imports/services/`**: OFX/CSV parsing and import orchestration
- **`templates/partials/`**: Reusable template components
- **`finance/components/`**: django-components for reusable UI elements

---

## 🎯 Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### CSS Development

When modifying the LUMA design system:

1. Edit `static/css/input.css`
2. Run `npm run css:build` to compile
3. Never edit `static/css/main.css` directly (it's generated)

### Design System Guidelines

- **Always use design system component classes** (`btn-primary`, `card`, `form-input`, etc.)
- **Dark-mode first**: All designs assume dark mode as the primary state
- **Glass panels**: Use `card` class for standard glass panels with backdrop blur
- **Semantic colors**: Use `text-emerald-400` for assets/gains, `text-rose-400` for liabilities/losses
- **Typography**: Use `font-mono` for all monetary values, percentages, and dates

---

## 🎨 Design Philosophy

### Voice & Tone

- **Precise**: We don't guess. We calculate. "Net Worth is R$ 1.2M," not "You have about a million."
- **Ambient**: We inform, we don't shout. Notifications are pulses, not alarms.
- **Optimistic**: The future is bright. Upward trends glow; downward trends are muted but clear.
- **Intelligent**: We speak like a high-end concierge, not a bank teller.

### Interaction Patterns

- **Spotlight Hover**: Interactive cards implement a radial gradient that follows the cursor
- **Progressive Disclosure**: Show totals, hide details until requested
- **Skeleton Loading**: Never show a white screen—use `bg-white/5` pulse animations
- **Fluid Transitions**: Objects fade and slide (translateY) as if moving through a medium

---

## 🌍 Migration from Ruby on Rails

This Django application is a port of the original Maybe Rails application. Key differences:

- **Single-user**: No Family multi-tenancy (simplified to User)
- **Brazil-first**: Default currency BRL, date format DD/MM/YYYY, B3 ticker support
- **OFX/CSV Import**: Replaces Plaid integration for Brazilian banks
- **HTMX**: Replaces Hotwire/Turbo for SPA-like interactions
- **LUMA Design System**: Custom Ethereal Dark Mode aesthetic with glass morphism
- **Simplified**: Removed Stripe billing, Plaid integration, and other US-specific features

---

## 📄 License

This project is distributed under the **AGPLv3** license.

---

## 🎭 Identity Statement

> **Luma is the signal in the noise.** It is built for the user who values clarity, speed, and privacy. It is not a tool for accounting; it is a tool for wealth generation.

---

*Built with precision. Designed for clarity. Powered by light.*
