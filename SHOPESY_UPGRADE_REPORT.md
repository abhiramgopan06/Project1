# ShopEasy upgrade report

This upgrade keeps the existing Django app structure and adds features incrementally.

## Changes in this build

- Product reviews now have moderation fields and a verified-purchase flag. Reviews submitted from the delivered-order review flow are marked verified and await moderation; only approved reviews appear publicly.
- Added order tracking event and abandoned-cart reminder consent models. Consent defaults to off.
- Added an owner-scoped PDF invoice/receipt endpoint with itemized totals; install dependencies from `requirements.txt`.
- Verified checkout payment submissions now reject a payment ID that has already been processed, create an initial tracking history, create a payment record, and record a staff activity event. Razorpay webhook handling ignores duplicate captured events already recorded as successful.
- Existing variant stock, stock history, returns workflow, reports, analytics, and product gallery are retained.

## Setup

1. Back up `db.sqlite3` before migrations. Do not delete the database.
2. Activate your virtual environment and install dependencies: `pip install -r requirements.txt`.
3. Run `python manage.py check`.
4. Run `python manage.py makemigrations` only if Django reports model changes not covered by the included migrations.
5. Run `python manage.py migrate`.
6. Run `python manage.py test`.
7. In Django admin, review submitted product reviews and set `is_approved` only after moderation.

## Not fully automated / needs configuration or further work

- The tracking timeline displays recorded events; a complete staff workflow to set every stage and timestamp still needs to be connected to the order-processing UI.
- Abandoned-cart consent storage is present, but the scheduled reminder job, opt-in UI, and email delivery task are not wired in this build.
- Shipping retains the existing free/express choices and tracking fields. Live PIN-code serviceability and courier integration require a configured provider or maintained serviceability table.
- Refund processing must be confirmed with the payment provider; a staff status flag alone is not proof of a real refund. Refund references/provider API integration remain dependent on payment credentials and provider support.
- Staff groups/permissions, bulk editing UX, expanded CSV/Excel coverage, and the full security/test matrix need further implementation and verification.

## Verification status

Python source files can be syntax-compiled, but Django could not be installed in the working environment because package downloads were unavailable. Consequently Django system checks, migrations, database compatibility, and runtime tests have **not** been verified here. Run the commands above locally before deploying.
