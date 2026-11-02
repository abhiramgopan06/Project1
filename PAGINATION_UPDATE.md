# Pagination update

ShopEasy list pages now show at most 12 records per page. When there are 12 or fewer records, the pagination controls stay hidden. Larger lists use a compact pager with previous/next arrows, page numbers, and a page count.

The shared pager is in `templates/includes/pagination.html`, and the query-string helper is in `storeextras/templatetags/pagination_tags.py`. It preserves active search and filter values while changing pages.

Updated lists include the storefront product grid, customer payment history, return history, wishlist, notifications, order history, admin payment/order/product/user/category lists, return management, activity and stock history, offer tables, and offer-history pages.

## Local verification

Activate your project's virtual environment and run:

```powershell
python manage.py check
python manage.py test
python manage.py runserver
```

Test each list with more than 12 records and confirm that filters remain selected when moving between pages. This archive was syntax-compiled, but the full Django checks and database tests must be run in the project's own environment.
