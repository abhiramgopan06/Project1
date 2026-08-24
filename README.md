# E-Comerce Store — Django E-Commerce Application

A full-stack e-commerce web application built with Django, featuring separate **Admin** and **User** roles, product browsing with search/filtering, a persistent cart, order placement with delivery details, order status tracking, and both Cash-on-Delivery and online (Razorpay demo) payment options.

---

## Table of Contents

- Features
- Tech Stack
- Project Structure
- Database Design
- Setup & Installation
- Environment Variables
- Running the Project
- User Roles & Access
- App-by-App Overview
- Order Status Flow
- Payment Flow
- Error Handling
- Known Limitations

---

## Features

### Admin
- Secure login (staff-only access to the dashboard)
- Custom admin dashboard — store stats, revenue, low-stock alerts, recent orders
- Add / update / delete products and categories (via Django Admin)
- Upload and manage product images
- Manage product stock and availability
- View all registered users and their order counts
- View all customer orders, filter by status
- Update order status (Pending → Confirmed → Shipped → Delivered / Cancelled)
- View basic sales/revenue information

### User
- Register an account, log in / log out
- View and edit profile (name, email, phone, address, city, state, pincode)
- Browse products, view product details
- Search products by name/description
- Filter products by category and price range
- Add products to cart, update quantities, remove items
- View live cart total
- Checkout with a delivery address
- Pay by Cash on Delivery or online (demo payment gateway)
- View past orders and full order details
- Track order status with a visual progress tracker

---

## Tech Stack

| Layer            | Technology                          |
|-------------------|--------------------------------------|
| Backend           | Django 5.x (Python)                  |
| Database          | SQLite (default, swappable)          |
| Frontend          | Django Templates, HTML, CSS, vanilla JS |
| Image handling    | Pillow                               |
| Online payments   | Razorpay SDK (demo/sandbox mode)     |

---

## Project Structure

```
project1/
├── ecommerce/          # Project settings, root URLs
├── accounts/           # Registration, login/logout, profile
├── products/           # Product & category models, browsing, search/filter
├── cart/                # Cart & cart item management
├── orders/             # Checkout, order history, order detail/tracking
├── payments/           # Online payment (demo) integration
├── dashboard/           # Staff-only admin dashboard
├── templates/           # Shared templates (base.html, 404, 500, etc.)
├── static/css/          # Stylesheet
├── media/               # Uploaded product images (created at runtime)
├── requirements.txt
└── manage.py
```

Each Django app follows the same internal layout: `models.py`, `views.py`, `urls.py`, `admin.py`, `forms.py` (where relevant), `migrations/`, and its own `templates/<app_name>/` folder.

---

## Database Design

**Core relationships:**

```
User (Django auth) ──1:1── UserProfile

User ──1:1── Cart ──1:N── CartItem ──N:1── Product ──N:1── Category

User ──1:N── Order ──1:N── OrderItem ──N:1── Product
```

- **Product** — name, description, price, category (FK), image, stock, is_available, created_at, updated_at
- **Category** — name
- **Cart / CartItem** — one cart per user; each cart item links a product to a quantity
- **Order / OrderItem** — snapshots the delivery details and payment info per order; each order item stores the price *at the time of purchase* (so later price changes don't affect historical orders)
- **Order.status** — choice field: `Pending`, `Confirmed`, `Shipped`, `Delivered`, `Cancelled`

Stock is decremented atomically at checkout (using `select_for_update`) to prevent overselling under concurrent orders.

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- pip

### 1. Clone / extract the project
```bash
cd project1
```

### 2. Create and activate a virtual environment
```bash
python -m venv env

# Windows
env\Scripts\activate

# macOS/Linux
source env/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply migrations
```bash
python manage.py migrate
```

### 5. Create an admin (staff) account
```bash
python manage.py createsuperuser
```

### 6. Run the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the storefront and `http://127.0.0.1:8000/dashboard/` for the admin dashboard (staff login required). The built-in Django admin is also available at `http://127.0.0.1:8000/admin/`.

---

## Environment Variables

The project reads the following from the environment, with safe local defaults if unset — so it runs out of the box for development, but should be configured properly for any real deployment:

| Variable               | Purpose                                  | Default (dev only)         |
|--------------------------|-------------------------------------------|-------------------------------|
| `DJANGO_SECRET_KEY`      | Django cryptographic signing key          | insecure dev key             |
| `DJANGO_DEBUG`           | Enable/disable debug mode                 | `True`                       |
| `DJANGO_ALLOWED_HOSTS`   | Comma-separated allowed hosts             | `127.0.0.1,localhost`        |
| `RAZORPAY_KEY_ID`        | Razorpay public key (demo)                | sandbox test key             |
| `RAZORPAY_KEY_SECRET`    | Razorpay secret key (demo)                | sandbox test key             |

For a real deployment, set these via your hosting platform's environment configuration rather than relying on the defaults, and set `DJANGO_DEBUG=False`.

---

## User Roles & Access

| Area                     | Who can access it                     |
|----------------------------|------------------------------------------|
| Storefront, cart, checkout | Any logged-in user                       |
| `/dashboard/*`              | Staff users only (`@staff_member_required`) |
| `/admin/*` (Django Admin)  | Staff/superuser (per Django's own rules)  |
| Order history / detail     | The order's owner only                    |

Non-staff users attempting to reach `/dashboard/` are redirected to login; a logged-in non-staff user is denied.

---

## App-by-App Overview

- **`accounts`** — registration form, login/logout (Django's built-in auth views), profile view/edit backed by a `UserProfile` model (phone, address, city, state, pincode).
- **`products`** — `Category` and `Product` models; home page with search (`?q=`), category filter, and price-range filter; product detail page.
- **`cart`** — add/remove/increase/decrease/set-quantity endpoints, all scoped to the logged-in user's own cart; stock is checked on every quantity change; a context processor exposes the live cart item count to the navbar on every page.
- **`orders`** — checkout view (COD path — atomic, locks cart items and products, decrements stock, computes the total server-side rather than trusting client input); order history and order detail (with a visual Pending→Confirmed→Shipped→Delivered tracker, or a Cancelled badge).
- **`payments`** — `create_payment_order` and `verify_payment` endpoints used by the checkout page's "Pay Online" flow (see Payment Flow below).
- **`dashboard`** — staff-only views: overview stats, order list with status-update dropdown, and a registered-users list.

---

## Order Status Flow

```
Pending → Confirmed → Shipped → Delivered
                              ↘
                             Cancelled
```

- New orders start as `Pending`.
- Staff update the status from the admin dashboard's Orders page.
- The user-facing order detail page shows a step tracker for the four "happy path" states, or a distinct badge if the order was `Cancelled`.

---

## Payment Flow

Two payment methods are offered at checkout:

1. **Cash on Delivery (COD)** — handled entirely by `orders.views.checkout`. The order is created with `payment_status='Pending'` and `status='Pending'`.

2. **Online payment (demo)** — handled by the `payments` app:
   - `create_payment_order` validates the cart and stock, then returns a simulated order reference (no real Razorpay order is created).
   - The checkout page shows a demo payment popup.
   - `verify_payment` then creates the `Order` (status `Confirmed`, payment status `Paid`), creates the `OrderItem`s, and decrements stock — all inside a single atomic transaction with row locking, the same as the COD path.

> **Note:** The online payment integration runs in **demo mode**. It does not contact Razorpay's servers or verify a real payment signature — it exists to demonstrate the checkout UX and the order-creation logic for an online payment path. Razorpay credentials are read from environment variables (see above) and are not required for the demo flow to work.

---

## Error Handling

- Form-level validation with inline error messages (registration, profile, checkout).
- Stock and quantity checks throughout the cart and checkout flow, with user-facing messages rather than silent failures or server errors.
- Custom `404.html` and `500.html` templates so unexpected errors show a branded page instead of a raw traceback (only visible in production, i.e. when `DEBUG=False`).
- Checkout and payment verification are wrapped in database transactions, so a failure partway through never leaves a half-created order or incorrect stock count.

---

## Known Limitations

- The online payment flow is a **demo/simulation**, not a production payment integration — see Payment Flow.
- Product, category, and stock management is done through Django's built-in Admin site rather than a custom-built product editor in the staff dashboard.
- SQLite is used by default; swap `DATABASES` in `ecommerce/settings.py` for a production database (e.g. PostgreSQL) before deploying.
