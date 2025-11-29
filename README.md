# Maybe Django - Personal Finance App

A Django port of the Maybe personal finance application, optimized for Brazil.

## Overview

This is a personal finance application built with Django, featuring:
- Account management (checking, savings, credit cards, investments, loans, properties, vehicles)
- Transaction tracking with automatic categorization
- Balance calculation and historical tracking
- Rules engine for automatic transaction categorization
- Budget management
- OFX/CSV import for Brazilian banks
- Installment support for credit card purchases
- B3 investment tracking (Brazilian stock market)
- HTMX for SPA-like interactions
- Tailwind CSS v3.4+ with custom design system for styling

## Requirements

- Python 3.10+
- PostgreSQL 12+
- Redis (for Celery background tasks, optional)

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd maybe_django
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. Create PostgreSQL database:
```bash
createdb maybe_django
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Build CSS (required before first run):
```bash
npm install
npm run css:build
```

8. Run development server:
```bash
python manage.py runserver
```

## Project Structure

- `maybe_django/core/` - User authentication and core models
- `maybe_django/finance/` - Accounts, transactions, balances, categories, rules, budgets
- `maybe_django/investments/` - Securities, holdings, trades
- `maybe_django/imports/` - OFX/CSV file importers

## Features

- Personal finance tracking (single-user, no multi-tenant complexity)
- OFX/CSV import for Brazilian banks
- Installment support for credit card purchases
- B3 investment tracking (Brazilian stock market)
- HTMX for SPA-like interactions
- Tailwind CSS v3.4+ with custom design system for styling
- Rules engine for automatic transaction categorization
- Budget management with category tracking

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Migration from Ruby on Rails

This Django application is a port of the original Maybe Rails application. Key differences:

- **Single-user**: No Family multi-tenancy (simplified to User)
- **Brazil-first**: Default currency BRL, date format DD/MM/YYYY, B3 ticker support
- **OFX/CSV Import**: Replaces Plaid integration for Brazilian banks
- **HTMX**: Replaces Hotwire/Turbo for SPA-like interactions
- **Simplified**: Removed Stripe billing, Plaid integration, and other US-specific features

## License

This project is distributed under the AGPLv3 license.
