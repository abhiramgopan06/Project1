PROJECT 1 - E-COMMERCE SHOP: REVIEW AND IMPROVEMENTS

Included improvements
- Refined the storefront hero, product cards, category cards, focus states, and mobile layout.
- Improved shared dashboard card and table styling.
- Added request-aware staff attribution to stock movement tracking. Stock changes made through a signed-in staff dashboard are associated with the correct staff member instead of guessing which unassigned stock record is newest.
- Kept staff activity monitoring limited to staff accounts and kept stock movement records filterable by staff member.
- Changed the product delete action to archive a product by making it unavailable. This preserves order items and product offer history instead of deleting historical records through cascading database relationships.
- Removed source comments from Python, HTML templates, and CSS.

Run locally
1. Extract this ZIP.
2. Open the project1 folder in VS Code.
3. Activate your virtual environment.
4. Install dependencies: pip install -r requirements.txt
5. Run: python manage.py check
6. Run: python manage.py migrate
7. Run: python manage.py runserver

Testing note
Python files compile successfully with Python's compileall. A full Django system check could not be executed in this build environment because Django dependencies were not installed and package network access was unavailable. Run the commands above locally and test customer checkout, staff product updates, offer changes, returns, and admin staff monitoring before using this as your only copy.

Security note
Set a strong DJANGO_SECRET_KEY and DJANGO_DEBUG=False before deployment. Keep .env out of source control. The project is intended for local development until production security settings and payment/email credentials are reviewed.

Additional review fixes
- Dashboard product counts now represent available products, and low-stock panels no longer include archived listings.
- Product search-history matching ignores archived products.
- Staff monitoring keeps relevant historical staff-operation records visible after an account's staff role is revoked; stock movements are retained in the admin view for non-superuser actors.
- Added consistent keyboard-focus indicators and restrained hover feedback for storefront cards.

Known limitations
- Activity tracking records operations made through the application's instrumented views and model signals. Direct database edits or changes made through uninstrumented scripts cannot be attributed reliably.
- Full end-to-end testing still needs to be run in the user's local environment with the required packages and database.


Latest layout correction
- Removed the automatic top margin from product prices that was stretching the space above the Add to Cart button.
- Product action buttons now remain together with an 8px gap.
- Removed fixed minimum heights that made product details areas unnecessarily tall.
- Set STATIC_URL to an absolute /static/ path for predictable local static-file URLs.


Product card refinement (2026-10-27): Product listing cards and homepage carousels use a more compact image area, tighter spacing, responsive grid columns, consistent action buttons, and a smaller circular wishlist heart. The heart stays in the upper-right of the product image and saved items retain the filled red heart state.
