# Project 1 — E-Commerce Shop

## Run the project locally

1. Open this folder in VS Code.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and fill in only the credentials you want to use.
5. Run `python manage.py check`.
6. Run `python manage.py migrate`.
7. Run `python manage.py runserver` and open `http://127.0.0.1:8000/`.

If you are using an existing database, make a backup of `db.sqlite3` before running migrations.

## Improvements in this revision

- Refined storefront spacing, responsive layout, product cards, product images, category cards, filters, and carousel cards.
- Fixed the all-products grid so cards use content-based row heights instead of leaving large empty spaces.
- Improved small-screen layout and keyboard focus visibility.
- Removed source comments from Python, HTML, and CSS files.
- Removed the local `.env` file from the archive and replaced the email address in the example configuration with a placeholder.
- Kept the existing app modules, migrations, product media, and SQLite database.

## Important testing notes

Python files compile and the included SQLite database passes its integrity check. Django's full system check and browser-based workflow tests were not run in this build environment because Django is not installed here. After installing requirements, test registration/email OTP, login/logout, product/category management, filters, pagination, cart, checkout, payment configuration, orders, returns/replacements, and staff permissions.

This project is intended for local development. Before deploying publicly, set a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and appropriate `DJANGO_ALLOWED_HOSTS`; configure email/payment credentials securely; and review production security settings.
