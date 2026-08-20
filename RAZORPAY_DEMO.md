# Razorpay Demo Payment Setup

This project uses Razorpay Standard Checkout in **Test Mode**.

## 1. Get Razorpay Test API keys

1. Open the Razorpay Dashboard.
2. Switch the Dashboard to **Test Mode**.
3. Go to **Account & Settings → API Keys**.
4. Generate a Test Key.
5. Put the credentials in your environment:

```text
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
```

Do not put the Key Secret in JavaScript or commit it to Git.

## 2. Install and run

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open the checkout page in the browser.

## 3. Demo the payment

1. Add a product to the cart.
2. Open **Checkout**.
3. Enter the customer name, email, phone and address.
4. Select **Online Payment**.
5. The button changes to **Pay Online**.
6. Click **Pay Online**.
7. The website asks Django to create a Razorpay Order.
8. Razorpay Checkout opens.
9. Complete the payment using Razorpay's Test Mode payment details.
10. Razorpay returns the payment ID, order ID and signature.
11. Django verifies the signature on the server.
12. If verification succeeds, the order is created as **Paid** and the cart is cleared.

### Easy UPI demo

In Razorpay Test Mode, use:

- Success: `success@razorpay`
- Failure: `failure@razorpay`

For cards, use the test-card details from Razorpay's official test-card documentation.

No real money is deducted in Test Mode.

## 4. Important

The application creates the Razorpay order on the server and verifies the returned signature on the server before creating the paid order.

For production, replace the Test Mode keys with Live Mode keys only after completing Razorpay's go-live requirements.
