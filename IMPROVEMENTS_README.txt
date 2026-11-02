PROJECT 1 - REVIEW SUMMARY

Changes retained in this package
- Updated storefront styling for a more polished home page, product cards, category cards, and mobile layouts.
- Improved shared dashboard styling, forms, tables, keyboard focus states, and responsive behavior.
- Preserved order history by archiving products instead of deleting records that may be referenced by orders.
- Improved staff attribution for stock changes made through supported dashboard workflows.
- Removed source comments from Python, HTML, CSS, and JavaScript files.
- Removed local virtual environments, Git internals, Python bytecode/cache folders, static build output, and the private .env file.
- Added a beginner-friendly START_HERE.txt setup guide.

Validation completed
- All Python files compile successfully.
- ZIP structure and archive integrity are checked after packaging.
- The project was not run end-to-end here because Django is not installed in the build environment.

Please verify locally
1. Run: python manage.py check
2. Run: python manage.py migrate
3. Run: python manage.py runserver
4. Test email OTP with your own .env settings.
5. Test customer and staff workflows, checkout, Razorpay test mode, returns, and role permissions.

Security
- Never share a real .env file or payment/email credentials.
- Before public deployment, configure a strong DJANGO_SECRET_KEY, DEBUG=False, allowed hosts, HTTPS/security settings, and production email/payment credentials.

LATEST HOME PAGE UPDATE
- Removed the extra "Find your products" filter panel from the top of the home page.
- Kept the main product listing and its search, category, price, and sort controls so shoppers can still filter products.
- Compiled Python source files successfully during this update. A live Django check still requires installing requirements.txt in the local environment.

HOME PAGE UPDATE - 2026-10-29
- Removed the home page product search and filtering panel shown above the product listing.
- Expanded the product listing to use the full available content width and adjusted responsive grid columns.
- Kept category navigation, product cards, wishlist, cart actions, and pagination.
- Removed the now-unreachable price-filter error message from the home page template.

Recently Viewed update (2 Nov 2026)
- The home page now lists up to 8 available products the signed-in customer has actually opened.
- Recently Viewed is filtered to the current signed-in user and sorted by most recent product view, not general cart/search interaction.
- Products are no longer hidden from Recently Viewed merely because they also appear in the current All Products page.
- Anonymous visitors do not see another account's history; the section appears after they sign in and view products.
- Added automated tests for account isolation, newest-first ordering, and anonymous visitors.
