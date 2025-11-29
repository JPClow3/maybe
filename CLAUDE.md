# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Development Server
- `cd maybe_django && python manage.py runserver` - Start Django development server
- `cd maybe_django && python manage.py shell` - Open Django shell
- `cd maybe_django && python manage.py shell_plus` - Open Django shell with auto-imports (if django-extensions installed)

### Testing
- `cd maybe_django && python manage.py test` - Run all tests
- `cd maybe_django && python manage.py test finance` - Run tests for finance app
- `cd maybe_django && python manage.py test finance.tests.AccountTestCase.test_account_creation` - Run specific test
- `cd maybe_django && python manage.py test --verbosity=2` - Run tests with verbose output

### Linting & Formatting
- `npm run lint` - Check JavaScript/TypeScript code with Biome
- `npm run lint:fix` - Fix JavaScript/TypeScript issues
- `npm run format` - Format JavaScript/TypeScript code
- `npm run style:check` - Check code style with Biome
- `npm run style:fix` - Fix code style issues

### CSS Build
- `npm run css:build` - Build Tailwind CSS from `maybe_django/static/css/input.css` to `maybe_django/static/css/main.css`
- `npm run css:watch` - Watch for changes and rebuild CSS automatically

### Database
- `cd maybe_django && python manage.py makemigrations` - Create new migration files
- `cd maybe_django && python manage.py migrate` - Apply pending migrations
- `cd maybe_django && python manage.py migrate finance zero` - Rollback all migrations for finance app
- `cd maybe_django && python manage.py showmigrations` - Show migration status
- `cd maybe_django && python manage.py sqlmigrate finance 0001` - Show SQL for a migration

### Background Tasks (Celery)
- `cd maybe_django && celery -A maybe_django worker -l info` - Start Celery worker
- `cd maybe_django && celery -A maybe_django beat -l info` - Start Celery beat scheduler

### Setup
- `cd maybe_django && pip install -r requirements.txt` - Install Python dependencies
- `cd maybe_django && python manage.py createsuperuser` - Create admin user

## Pre-Pull Request CI Workflow

ALWAYS run these commands before opening a pull request:

1. **Tests** (Required):
   - `cd maybe_django && python manage.py test` - Run all tests (always required)

2. **Linting** (Required):
   - `npm run lint` - JavaScript/TypeScript linting
   - `npm run style:check` - Code style checking

3. **Code Quality** (Recommended):
   - Ensure all migrations are created for model changes
   - Check for Python syntax errors

Only proceed with pull request creation if ALL checks pass.

## General Development Rules

### Authentication Context
- Use `request.user` for the current user in views and templates
- User authentication is handled via Django's built-in authentication system
- Single-user application (no multi-tenant Family model)

### Development Guidelines
- Prior to generating any code, carefully read the project conventions and guidelines
  - Read [project-design.mdc](mdc:.cursor/rules/project-design.mdc) to understand the codebase
  - Read [project-conventions.mdc](mdc:.cursor/rules/project-conventions.mdc) to understand _how_ to write code for the codebase
  - Read [ui-ux-design-guidelines.mdc](mdc:.cursor/rules/ui-ux-design-guidelines.mdc) to understand how to implement frontend code specifically
- Ignore i18n methods and files. Hardcode strings in English for now to optimize speed of development (even though app defaults to pt-BR)

## Prohibited Actions

- Do not run `python manage.py runserver` in your responses
- Do not automatically run migrations
- Do not run `python manage.py createsuperuser` in your responses

## High-Level Architecture

### Application Mode
The Maybe Django app is a single-user personal finance application optimized for Brazil. It does not support multi-tenancy.

### Core Domain Model
The application is built around financial data management with these key relationships:
- **User** → has many **Accounts** → has many **Transactions**
- **Account** types: checking, savings, credit cards, investments, loans, properties, vehicles
- **Transaction** → belongs to **Category**, can have **Tags** and **Rules**
- **Investment accounts** → have **Holdings** → track **Securities** via **Trades**

### API Architecture
The application uses HTMX for SPA-like interactions:
- Server-rendered HTML templates with HTMX for dynamic updates
- No separate API layer for internal features
- Django templates serve HTML directly with HTMX enhancements

### Import System
Data ingestion methods:
1. **OFX Import**: Support for Brazilian bank OFX files
   - `Import` model manages import sessions
   - Supports transaction and balance imports
   - Automatic duplicate detection
2. **CSV Import**: Manual data import with mapping
   - Custom field mapping with transformation rules
   - Flexible format support

### Background Processing
Celery handles asynchronous tasks:
- Account syncing
- Balance calculations
- Investment price fetching (B3 market data)
- Scheduled tasks via Celery Beat

### Frontend Architecture
- **HTMX**: Server-side rendering with HTMX for reactive UI without heavy JavaScript
- **Django Components**: Reusable UI components using django-components
- **Tailwind CSS v3.4+**: Styling with custom design system built via PostCSS
  - Design system defined in `maybe_django/static/css/input.css` with component classes
  - Compiled to `maybe_django/static/css/main.css` using `npm run css:build`
  - Always use functional tokens and component classes (`btn-primary`, `card`, `form-input`, etc.) when available
  - Prefer semantic HTML elements over JS components
  - Build CSS with: `npm run css:build` or watch with: `npm run css:watch`

### Currency Support
- Single currency default: BRL (Brazilian Real)
- All monetary values stored as Decimal with 4 decimal places
- `Money` utility class handles formatting and calculations

### Security & Authentication
- Django's built-in session-based authentication
- CSRF protection enabled by default
- Strong password validation via Django validators
- Single-user application (no API authentication needed)

### Testing Philosophy
- Comprehensive test coverage using Django's built-in unittest framework
- Test models in `maybe_django/*/tests.py` files
- Keep tests minimal and focused on critical business logic
- Only test important code paths that significantly increase confidence

### Performance Considerations
- Database queries optimized with proper indexes
- N+1 queries prevented via `select_related()` and `prefetch_related()`
- Background jobs for heavy operations (Celery)
- Caching strategies for expensive calculations

### Development Workflow
- Feature branches merged to `main`
- Docker support for consistent environments (see `compose.example.yml`)
- Environment variables via `.env` files (use `python-decouple` or `os.environ.get()`)
- Django admin at `/admin/` for data management

## Project Conventions

### Convention 1: Minimize Dependencies
- Push Django to its limits before adding new dependencies
- Strong technical/business reason required for new dependencies
- Favor old and reliable over new and flashy

### Convention 2: Fat Models, Skinny Views
- Business logic in model methods and utility classes
- Views should be thin controllers that delegate to models/services
- Organize complex logic into service classes in `maybe_django/*/services/` directories
- Models should answer questions about themselves: `account.get_balance_series()` not `AccountService.get_balance_series(account)`

### Convention 3: HTMX-First Frontend
- **Native HTML preferred over JS components**
  - Use `<dialog>` for modals, `<details><summary>` for disclosures
- **Leverage HTMX for dynamic updates**
  - Use HTMX attributes (`hx-get`, `hx-post`, `hx-swap`, `hx-target`, `hx-boost`) for SPA-like interactions
  - Server-side rendering with selective DOM updates
  - Use partial templates for form submissions and dynamic content
  - Use `HX-Redirect` header for successful form submissions
- **Query params for state** over localStorage/sessions when possible
- **Server-side formatting** for currencies, numbers, dates
- Use django-components for reusable UI components
- Use design system component classes (`btn-primary`, `card`, `form-input`, etc.) from `maybe_django/static/css/input.css`

### Convention 4: Optimize for Simplicity
- Prioritize good domain design over performance
- Focus performance only on critical/global areas (avoid N+1 queries, mindful of global templates)

### Convention 5: Database vs Django ORM Validations
- Simple validations (null checks, unique constraints) in DB via model fields
- Django model validations for form convenience and business rules
- Complex validations and business logic in model methods or `clean()` methods

## Django Components

### Component vs. Template Decision Making

**Use django-components when:**
- Element has complex logic or styling patterns
- Element will be reused across multiple views/contexts
- Element needs structured styling with variants/sizes
- Element requires interactive behavior with HTMX

**Use regular templates/partials when:**
- Element is primarily static HTML with minimal logic
- Element is used in only one or few specific contexts
- Element is simple template content

## Testing Philosophy

### General Testing Rules
- Always use Django's unittest framework
- Keep tests minimal and focused
- Only write tests for critical and important code paths
- Write tests as you go, when required
- Take a practical approach - tests are effective when their presence significantly increases confidence

### Test Quality Guidelines
- Write minimal, effective tests
- Only test critical code paths
- Test boundaries correctly:
  - Commands: test they were called with correct params
  - Queries: test output
  - Don't test implementation details of other classes
