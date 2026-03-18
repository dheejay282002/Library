# Library Management System - Project Documentation

## 1. Overview
This project is a Django-based Library Management System with role-based access for students, admins, librarians, and POS operators.

It supports:
- Student registration and email verification
- Admin/librarian approval workflows
- Book and student management
- POS borrowing and return workflows
- CSV import/export for master data
- Dashboard analytics (including librarian charts)
- Email notifications (verification and transaction-related)

The system is currently configured to run primarily on XAMPP MariaDB/MySQL, with SQLite retained as a secondary database alias for data migration and tooling.

## 2. Core Features
### Authentication and Identity
- Custom user model with role-based user type:
  - `student`
  - `admin`
  - `librarian`
  - `pos`
- Login and logout
- Student ID pre-verification before registration
- Email code verification for student onboarding

### Student Lifecycle
- Student preloaded records (manual or CSV)
- Student self-registration tied to existing student ID
- Verification code generation and expiration handling
- Admin approval/rejection flow

### Library Catalog and Borrowing
- Book catalog with metadata (ISBN, title, author, category, shelf, copies, cover)
- Inventory tracking (`copies_total`, `copies_available`)
- Transaction + transaction item model for multi-book borrow requests
- Approval workflow for pending transactions
- Return flow with status updates

### Role Dashboards
- Student dashboard for account and borrowing access
- Admin dashboard for system-level operations
- Librarian dashboard with KPI cards and visualization charts:
  - Most borrowed books
  - Borrowing by category
  - Monthly borrowing trend
  - Borrowed vs returned split
- POS dashboard for front-desk operations

### Data Operations
- CSV import:
  - Books
  - Students
- CSV export:
  - Books by category
- Sample CSV templates and import guide available

### Communications
- SMTP-backed email sending
- Verification and approval/rejection-related email flows
- Reminder command scaffold included (`send_reminders`)

## 3. Tech Stack
- Python 3.11+
- Django (runtime currently observed as 6.0.3)
- MySQL/MariaDB via XAMPP (PyMySQL bridge)
- Tailwind-compatible Django forms (`crispy-tailwind`, `django-crispy-forms`)
- Pillow for media/image handling
- WhiteNoise for static file serving support

Frontend charting:
- Chart.js via CDN in librarian dashboard

## 4. Project Architecture
### Main Django Project
- `library_system/`
  - `settings.py`: app configuration, DB configuration, static/media, auth model
  - `urls.py`: root URL wiring (`django-admin/` + app URLs)
  - `__init__.py`: PyMySQL registration and compatibility patches

### Main App
- `library/`
  - `models.py`: domain models and relations
  - `views.py`: role workflows and feature endpoints
  - `forms.py`: form and validation definitions
  - `urls.py`: route map
  - `context_processors.py`: system settings injected globally
  - `templates/library/`: UI templates
  - `management/commands/send_reminders.py`: reminder command

### Supporting Documents
- `CSV_IMPORT_GUIDE.md`: CSV format and import behavior
- `DATABASE_DOCUMENTATION.md`: ERD and schema-level reference

## 5. Data Model Summary
Primary models:
- `User` (custom auth model)
- `Student` (profile + approval + verification flags)
- `Book` (catalog + inventory)
- `Transaction` (borrow request header)
- `TransactionItem` (borrow request items)
- `VerificationCode` (email verification)
- `Librarian` (staff profile)
- `POS` (operator profile)
- `SystemSettings` (name/tagline/logo)
- `AdminLog` (auditable actions)
- `LibraryStatus` (open/closed/maintenance/holiday)

Key relationships:
- `User` one-to-one with role profiles (`Student`, `Librarian`, `POS`) where applicable
- `Student` one-to-many `Transaction`
- `Transaction` one-to-many `TransactionItem`
- `TransactionItem` many-to-one `Book`

## 6. Role-Based Capabilities
### Student
- Register and verify email
- Access student dashboard
- Browse books and request borrowing (workflow-dependent routes)

### Admin
- Approve/reject student registrations
- Manage books, students, librarians, and POS accounts
- Review logs
- Handle transaction approvals
- Configure system settings

### Librarian
- Operational dashboard
- Book/student management
- Import/export support
- Transaction queue handling
- Borrowing analytics charts

### POS
- Validate student and books
- Create borrowing transactions
- Process returns

## 7. URL and Module Coverage
Primary URL groups in `library/urls.py`:
- Authentication and verification endpoints
- Dashboard endpoints (`student`, `admin`, `librarian`)
- Admin operations for books/students/librarians/POS/settings/logs
- POS operations (`borrow`, `return`, validation, success pages)
- AJAX endpoints for validation and reset-code flows

Note:
- The codebase includes some duplicated/legacy function blocks in `views.py` and repeated route declarations (for example, POS routes). The currently wired URLs remain functional, but cleanup is recommended.

## 8. Database Configuration
Current default:
- MySQL/MariaDB (`default`) for production/local XAMPP use

Secondary alias:
- SQLite (`sqlite`) for migration utilities and source-data import workflows

Configured DB settings (environment-aware):
- `MYSQL_DATABASE` (default: `library`)
- `MYSQL_USER` (default: `root`)
- `MYSQL_PASSWORD` (default: empty)
- `MYSQL_HOST` (default: `127.0.0.1`)
- `MYSQL_PORT` (default: `3306`)
- `SQLITE_DB_PATH` (optional override for SQLite source file)

## 9. Setup and Run (XAMPP/MySQL)
1. Start XAMPP services:
- Apache (optional for phpMyAdmin)
- MySQL/MariaDB

2. Ensure database exists in MySQL:
- DB name should match `MYSQL_DATABASE` (default `library`)

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate --fake-initial
```

5. Create admin account:
```bash
python manage.py createsuperuser
```

6. Start development server:
```bash
python manage.py runserver
```

## 10. Data Migration: SQLite -> MySQL
The project supports migration from SQLite using the secondary `sqlite` DB alias.

Typical workflow:
1. Export from SQLite source:
```bash
python manage.py dumpdata <app/model list> --database=sqlite --indent 2 --output sqlite_to_mysql_library.json
```

2. Load into MySQL default:
```bash
python manage.py loaddata sqlite_to_mysql_library.json --database=default
```

3. Validate counts via Django shell:
```bash
python manage.py shell
```

## 11. Email and Notification Behavior
Configured with SMTP backend and Gmail host values in settings.

Main use cases:
- Student verification code
- Approval/rejection notices
- Borrow/return related communication paths

Reminder command:
```bash
python manage.py send_reminders
```

Operational note:
- Current reminder command references transaction-book access inconsistent with the `Transaction`/`TransactionItem` schema and should be refactored before production scheduling.

## 12. Static and Media
- Static URL: `/static/`
- Media URL: `/media/`
- Media stores profile photos, book covers, POS/librarian photos, and system assets

## 13. Security and Production Hardening Checklist
Before production deployment, update:
- `DEBUG=False`
- `SECRET_KEY` from environment variable
- `ALLOWED_HOSTS` restricted to real domains
- SMTP credentials to environment variables only
- CSRF trusted origins for deployed domain(s)
- Password and sensitive defaults currently hardcoded in settings

Recommended:
- Add rate-limiting and brute-force protection on login/reset endpoints
- Add structured audit logging for all admin/librarian mutating actions
- Enforce HTTPS and secure cookie settings

## 14. Testing Status and Gaps
Current test module is minimal.

Recommended coverage additions:
- Auth and role access control tests
- Student registration/verification lifecycle tests
- Inventory consistency tests during approve/reject/return flows
- CSV import validation tests
- Dashboard analytics query tests

## 15. Known Codebase Notes
Observed technical debt areas:
- Duplicate imports and duplicate function blocks in `views.py`
- Duplicate/legacy route declarations in `urls.py`
- Runtime Django version differs from pinned requirement entry
- XAMPP MariaDB compatibility patches are implemented in project init

These do not block current operation but should be cleaned for maintainability.

## 16. Recommended Next Improvements
- Split `views.py` into domain modules (`auth`, `admin_ops`, `librarian_ops`, `pos_ops`, `student_ops`)
- Introduce service layer for transaction approval/inventory updates
- Add API endpoints for chart data and async dashboard loading
- Add CI checks for linting, tests, and migration consistency
- Normalize dependencies and lock runtime versions

---

## Appendix A: Key Documentation Files
- `CSV_IMPORT_GUIDE.md`
- `DATABASE_DOCUMENTATION.md`

These complement this document with deep CSV/schema specifics.

---

Generated for siyempre, sa Klase namin, sir Mark pa naman, so this is our repository documentation.