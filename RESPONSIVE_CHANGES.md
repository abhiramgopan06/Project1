# Responsive Design Changes

This version keeps the existing desktop design and adds simple, beginner-friendly responsive rules.

## Main changes
- Product grids show **2 product cards per row on phones**.
- Product cards, images, prices and buttons are smaller on phones.
- Featured product carousel shows **2 products at a time on phones**.
- Navbar stacks the shop name, search box and navigation links on small screens.
- Category cards use two columns on phones.
- Filters move above products on smaller screens.
- Product detail page stacks image and information on phones.
- Cart items and order summary become easier to read on small screens.
- Checkout, login/register, profile and address sections use smaller padding.
- Admin dashboard navigation becomes a compact two-column menu on phones.
- Tables use horizontal scrolling instead of breaking the page.
- Footer changes to a mobile-friendly column layout.

The changes are mainly in `static/css/style.css`, with the mobile carousel count updated in `templates/products/home.html`.

### iPhone SE / very small phone footer update
- At widths up to 380px, the footer remains a two-column layout instead of becoming one long column.
- Footer headings and links are reduced slightly so the four footer sections fit comfortably.
- Social icons remain compact and wrap naturally into multiple rows.
- Copyright and payment methods are placed in separate rows to prevent horizontal overflow.
- The existing two-product-per-row mobile product layout is preserved at this width.
