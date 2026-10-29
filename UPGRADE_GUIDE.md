# Project 1 upgrade guide

## Setup
1. Back up your original project and database.
2. Create and activate a virtual environment.
3. Run `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set a unique `DJANGO_SECRET_KEY`.
5. Run `python manage.py migrate`.
6. Run `python manage.py check` and `python manage.py test`.
7. Start with `python manage.py runserver`.

## Improvements included
- Search, price/category filters and sorting.
- Product gallery and variant data models.
- Coupon definitions and apply/remove endpoints.
- Recently viewed products page based on existing product history.
- Verified reviews restricted to delivered orders.
- Order tracking fields and a customer cancellation endpoint.
- Sales analytics and order/stock CSV exports.
- Read-only REST API for products/categories and the signed-in user's orders.
- Product image/variant/coupon admin registration.

## Important limitations before production
- Existing wishlist, address book, return requests, order history and recommendations remain.
- Product variants are stored and displayed but are not yet fully selected through cart, stock deduction, and order-item snapshots. Do not use variant stock for real sales until that workflow is completed.
- Coupon application endpoints store a coupon in the session, but coupon discounts are not yet included in checkout totals/order creation. Treat coupons as a data model and interface starter, not production-ready discounting.
- The existing payment path is demo-only in development. Configure and test real Razorpay order creation, server-side signature validation, and provider webhooks before live use.
- Cancellation restores base product stock; prepaid refunds must be handled through Razorpay and the current cancellation endpoint is not a complete refund workflow.
- CSV exports are included. Excel export dependency is included but Excel download views are not yet wired.
- Order email notifications and automated low-stock email alerts still need configuration and integration.
- Use a production database, HTTPS, secure cookies, email credentials, allowed hosts, static/media storage and backups before deployment.

## API examples
- `/api/products/`
- `/api/categories/`
- `/api/my-orders/` (requires login)

## Beginner tip
Test one workflow at a time in a separate development database. Do not manually edit the live database.
