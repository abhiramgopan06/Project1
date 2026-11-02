# ShopEasy Payment History Style Update

- Payment History now follows the Returns & Refunds page layout and wider content width.
- The customer-facing Payment History table no longer displays a Customer column.
- The administrator payment table remains separate and can continue to show customer identity.
- The table keeps horizontal scrolling on narrower screens.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your own settings/secrets.
4. Run `python manage.py check`, then `python manage.py migrate`, then `python manage.py runserver`.

Back up your local database and `.env` before copying updated files over an existing project. Payment provider actions must be tested using your own credentials.
