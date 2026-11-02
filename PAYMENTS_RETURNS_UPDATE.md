# Payment History and Returns & Refunds update

- Redesigned customer Payment History and Returns & Refunds pages with responsive layouts, summary cards, filters, clear empty states, status badges, and order links.
- Added filtering by payment status, payment method, order number, or payment reference.
- Added filtering by return status and request type.
- Cash-on-delivery orders now create a pending payment record so they can appear in Payment History.
- The returns page shows request, inspection, and refund information. Staff must still complete and confirm real online refunds through the payment provider; changing the application status alone does not move money.

After replacing the project files, activate your virtual environment and run:

```powershell
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py test
python manage.py runserver
```

Back up `db.sqlite3` and `.env` before replacing files. Do not delete migration files or use `--fake` to bypass migration errors.

## Payment history detail upgrade

- Payment history now shows customer name, email, product thumbnail, product name, quantity, transaction reference, payment date, method, amount, status, order link, and a View Details action.
- The detail page displays all order items with images, quantities, variants, unit and line prices, customer/shipping information, transaction metadata, order status, order totals, and links to the order and invoice.
- The detail endpoint is scoped to the signed-in customer's own payment record. Searching supports payment reference, order ID, payment record ID, customer name, and product name while retaining active status/method filters.
- Payment amounts and statuses are application records; online settlement/refund must still be confirmed with the provider.
