# ShopEasy Feature Guide

## Product variants

When adding or editing a product in the dashboard, choose a category such as clothing, shoes, electronics, phones, laptops, or accessories. The **Product options and variant stock** section appears for those categories.

Add one row for each option that can be purchased:
- **Option type:** Size, Color, Storage capacity, or Other.
- **Option value:** For example `XL`, `Black`, or `256 GB`.
- **Price:** Enter a final price for that option, or leave it empty to use the product's current selling price.
- **Stock:** Enter the quantity available for this exact option.
- **SKU:** Optional; ShopEasy creates one if left blank.

For clothing, create rows for sizes such as `S`, `M`, `L`, `XL`, and `XXL`. Only options you create with stock greater than zero can be purchased. The product page shows unavailable standard clothing sizes in grey. Options that have a row but zero stock also show a **Notify me** form.

Each product currently uses one primary option dimension per variant list (for example, size *or* color *or* storage). Separate combinations such as `Black / XL` should be added as distinct variants if you need both attributes together.

## Back-in-stock email alerts

Customers can enter an email address on an unavailable product or unavailable variant. When a staff member increases that product or variant's stock through a normal save, ShopEasy attempts to send an email. Signed-in customers also receive an in-app notification.

For real email delivery, copy `.env.example` to `.env` and configure the email values described in `OTP_EMAIL_SETUP.txt`. Without SMTP settings, Django uses the console email backend and prints messages in the terminal. The alert stays pending if the email backend reports that sending failed.

## Wishlist

The wishlist now has an introductory panel, product cards, and a saved-items summary panel. Customers can open product details, remove saved items, and choose options for variant products before adding them to the cart.

## Stock and checkout behavior

- Variant products use the selected variant's stock and price in the cart and checkout.
- Non-variant products continue to use the product-level stock and selling price.
- Order cancellation restores stock to the same variant that was ordered.
- Stock changes are recorded in the stock movement history.
- Back-in-stock alerts are triggered when stock increases.

## Database updates

The project includes migrations for variant option types and variant-specific prices, plus the `BackInStockAlert` model. Run:

```powershell
python manage.py migrate
python manage.py check
python manage.py test
```

Back up `db.sqlite3` and `media` before applying migrations to an existing copy of your project.

## Payment note

The demo payment flow is not a real payment processor. Configure and verify Razorpay server-side credentials and webhook behavior before accepting real payments or processing refunds.
