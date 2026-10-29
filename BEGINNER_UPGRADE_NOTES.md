# Beginner-friendly upgrade notes

## New features included
- Customer account dashboard with order, wishlist, return and notification counts.
- Product variants can be attached to order items; existing cart variant support is preserved.
- Stock reservation model for a future/explicit reservation workflow. Reservations expire and are indexed for cleanup queries.
- Razorpay webhook endpoint with HMAC signature validation and idempotent payment-record updates. Configure `RAZORPAY_WEBHOOK_SECRET` in `.env` and register `/payments/webhook/` with Razorpay.
- Excel exports for sales, inventory and return/refund records.
- Staff-only CSV product import endpoint. Required columns: `name,category,description,price,stock`.
- Production security flags when `DJANGO_DEBUG=False`.

## Important integration notes
- This project needs database migrations for the new `OrderItem.variant` field and `StockReservation` model. Run `python manage.py makemigrations products orders storeextras` and inspect the generated migrations, then `python manage.py migrate`.
- The current checkout workflow still uses the existing product-level stock field. Variant-level stock deduction and timed reservation/release must be wired into every cart and checkout path before selling variants live. The reservation model alone does not reserve stock automatically.
- Razorpay webhook endpoint updates payment records for captured/failed events, but full refund execution must still be performed through Razorpay's refund API and reconciled against provider responses. Never treat a local refund status as proof money was returned.
- CSV import is staff-only, validates required headers, and should be tested on a backup database before importing production data.
- Run tests and manual browser checks before deployment.

## Recommended commands
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```
