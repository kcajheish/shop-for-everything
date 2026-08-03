# Shop Code Review — Suggested Changes

Review date: 2026-08-03. Priorities are descending (P0 = fix first). Line numbers refer to the current `master`.

## P0 — Critical (security / data integrity)

> Status: all four P0 items FIXED on 2026-08-03. Verified by the test suite
> (`orders/tests.py`, `api/tests.py`, `shop/tests.py`) — run with `python manage.py test`.

### 1. Committed `SECRET_KEY` and `DEBUG=True` — FIXED
- `shop/settings.py:23,26` — the Django secret key is hardcoded and committed, and `DEBUG=True` is set unconditionally (also on EB production).
- Fix: generate `SECRET_KEY` from `os.environ.get('SECRET_KEY', ...)` and default `DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'`; rotate the key on EB (and note that the old one is in git history).
- Done: `SECRET_KEY` and `DEBUG` now come from env vars with a dev-only fallback key and `DEBUG=False` default. Remaining action: rotate the EB secret key, since the old one is in git history.

### 2. Unauthorized order access (IDOR) — FIXED
- `orders/views.py:51` — `order_detail` does `Order.objects.get(pk=order_id)` with no `customer` check; any logged-in user can read any order.
- Fix: filter to the requester, e.g. `get_object_or_404(Order, pk=order_id, customer=request.user)`, and add a test asserting other users get 404.
- Done: `order_detail` now uses `get_object_or_404(Order, pk=order_id, customer=request.user)`. Tests cover owner-200, other-user-404, anonymous-redirect.

### 3. Checkout is not atomic; email failure creates duplicate orders / stock corruption — FIXED
- `orders/views.py:13-37` — order + `OrderProduct` rows and stock decrement are not wrapped in `transaction.atomic`. `send_order_success_email(...)` is called synchronously (line 33) and raises when `SENDGRID_API_KEY` is missing, so the flow 500s *after* saving the order and decrementing stock but *before* `cart.clear()` — retrying checkout creates a duplicate order and double-decrements stock.
- Fix: wrap in `@transaction.atomic`; call the email task with `.delay()` (or in a `try/except`) so a mail failure never corrupts the sale; run stock decrement atomically (`Product.objects.filter(pk=..., stock__gte=qty).update(stock=F('stock')-qty)`) and verify the update affected a row before proceeding.
- Done: checkout is `@transaction.atomic` + `@require_http_methods(['POST'])`, stock is decremented with an atomic guarded `update(...)`, email is dispatched via `.delay()` inside a `try/except`, and empty carts redirect instead of creating empty orders. Tests cover success, insufficient-stock rollback, email-dispatch failure, GET rejection, and empty-cart redirect.

### 4. DRF API POST/PUT endpoints are broken (500) — FIXED
- `api/views.py:15,31,36` — typos `serializer.is_vaid()`, `serialzier.data`, `serailzier.is_valid()` raise `AttributeError`.
- Fix: correct the typos; also fix `return Response(serializer, ...)` (should be `serializer.data`).
- Done: typos fixed and `PUT` now calls `serializer.save()`. Tests cover POST-create, POST-400, PUT-update, PUT-400, and GET.

## P1 — High (crash bugs / wrong behavior)

> Status: all nine P1 items FIXED on 2026-08-03. Verified by regression tests
> (`products/tests/test_views.py`, `products/tests/test_models.py`, `cart/tests.py`,
> `users/tests.py`, `orders/tests.py`) — run with `python manage.py test`.

### 5. `product_detail` 500s on unknown slug
- `products/views.py:49` — `Product.objects.get(slug=slug)` raises `DoesNotExist` → 500.
- Fix: `get_object_or_404(Product, slug=slug)`.
- Done: unknown slugs now return 404. Test: `ProductDetailTest::test_unknown_slug_returns_404`.

### 6. Search crashes on a fresh session / bad input, and returns duplicates
- `products/views.py:82-83` — visiting `/product/search` without a `query` param and with no prior search raises `KeyError: 'query'`.
- Fix: `request.session.get('query', '')`.
- `products/views.py:86-89` — a multi-token query returns the same product once per matching token (duplicates), and an empty token matches everything (`name__icontains=''`).
- Fix: filter once with `Q` objects (`reduce(operator.or_, ...)`), and drop empty tokens.
- Done: `product_search` uses `request.session.get('query', '')`, drops empty tokens, and filters once with `Q`/`reduce` (no duplicates, no all-match). Tests: `ProductSearchTest`.

### 7. Pagination raises on bad/out-of-range page numbers
- `products/views.py:23,97` — `int(page_number)` raises `ValueError`; `paginator.page()` raises `EmptyPage` for out-of-range values (only prev/next are guarded).
- Fix: use `paginator.get_page(page_number)` (already computed as `product_list`) instead of `paginator.page(...)`, which returns the last page for out-of-range values.
- Done: `product_list` and `product_search` now use `paginator.get_page(...)`; `page=abc` → first page, out-of-range → last page. Tests: `PaginationTest`.

### 8. Cart update/delete crash on missing POST data or wrong method
- `cart/views.py:11-12,28-29` — `request.POST['quantity']` / `request.POST['is_processed']` / `request.POST['product_id']` raise `MultiValueDictKeyError` (500) when absent; `cart_delete` also runs on GET. `cart/decorators.py:7-8` has the same issue.
- Fix: add `@require_POST` to both views and read via `request.POST.get(...)` / validate the quantity.
- Done: `cart_update` is POST-only and `stock_should_enough` validates `1 <= quantity <= stock` (redirecting with a message); `cart_delete` is POST-only, reads `product_id` via `.get()`, and returns a safe JSON response. Tests: `CartDeleteTest`.

### 9. `Product.save()` image resize silently never runs; slug collisions 500
- `products/models.py:38-46` — `img.thumbnail(size)` returns `None` (it resizes in place), so `img_resize.save(...)` raises `AttributeError`, swallowed by bare `except: pass`. The 300x300 resize has never worked.
- Fix: `img.thumbnail(size); img.save(initial_path, quality=95)` and only swallow `IOError`.
- `products/models.py:34-35` — `save()` re-slugifies on every save, so two products with the same name produce the same slug → `IntegrityError` (unique constraint) → 500.
- Fix: only set the slug on create, and append a suffix (e.g. `-2`) on collision.
- Done: `Product.save()` only sets the slug on create (unique `-2`, `-3`, … suffix on collision, stable on update), and the resize now actually runs (`img.thumbnail(size)` + `img.save(...)`, only `IOError`/`OSError` swallowed; the shared `/default.jpg` placeholder is skipped). Tests: `ProductSlugTest`, `ProductImageResizeTest`.

### 10. `MinValueValidator` passed as a class, not an instance
- `orders/models.py:32-33` — `validators=[MinValueValidator]` (and same for `expense`) instantiates the class with the field value as `limit_value`, which never raises — validation is a silent no-op, so negative quantity/expense are accepted.
- Fix: `validators=[MinValueValidator(0)]`.
- Done: `OrderProduct.quantity` and `expense` now use `MinValueValidator(0)`. Tests: `OrderProductValidatorTest`.

### 11. Deleted products left in carts crash cart/checkout and orphan orders
- `cart/cart.py:43` — `Cart.__iter__` does `Product.objects.get(pk=...)`; deleting a product that's in a session cart → `DoesNotExist` → 500 on `/cart/detail` or checkout. `orders/views.py:17-18` iterates the cart after already saving the `Order`, so a failure leaves an empty orphan order.
- Fix: use `product_id__in=self.cart.keys()` with a queryset lookup and skip missing products; validate the cart is non-empty and all products exist before creating the `Order`.
- Done: `Cart.__iter__` fetches via `Product.objects.filter(pk__in=...)` and skips deleted items; checkout verifies every cart product still exists (redirects with a message before the `Order` is created). Tests: `CheckoutTest::test_checkout_redirects_when_cart_contains_deleted_product`, `test_cart_detail_renders_with_deleted_product`.

### 12. Product creation lets a user claim another author
- `products/forms.py:9` + `templates/products/create.html:74` — `author` is a client-controlled hidden form field; a POST can set `author` to any user id, spoofing ownership (which `product_delete` then trusts).
- Fix: remove `author` from `fields`, drop the widget, and set `form.instance.author = request.user` in `product_create`.
- Done: `author` removed from `ProductForm.fields` and from the template; `product_create` sets `product.author = request.user`. Test: `ProductCreateAuthorTest` (spoofed `author` is ignored).

### 13. Sign-up 500s when password fields are empty/invalid
- `users/forms.py:22-28` — `clean()` indexes `cd['password']` / `cd['password_confirm']`, but an empty (required) password is deleted from `cleaned_data` during field cleaning → `KeyError` → 500.
- Fix: `password = cd.get('password')` and guard with `if password and password_confirm`.
- Done: `SignUpForm.clean()` uses `.get()` with guards. Tests: `SignUpFormTest` (empty/mismatched passwords render the form instead of 500, valid signup still succeeds).

## P2 — Medium (correctness / robustness)

### 14. `Cart.add()` `update_quantity` semantics are inverted
- `cart/cart.py:18-21` — `update_quantity=True` **increments** and `False` **replaces**, the opposite of the name and of the canonical Django implementation. It works today only because the caller (`cart/views.py:15`) passes `True` for existing items. Latent footgun.
- Fix: swap the branches (replace on `True`, increment on `False`) and flip the caller.

### 15. Checkout GET / empty cart produce a "success" page
- `orders/views.py:14,37` — a GET to `/order/checkout` renders `success.html`, and an empty-cart POST creates an empty `Order`.
- Fix: make it `@require_POST`, and redirect back to the cart with a message when the cart is empty.

### 16. Negative or oversized quantities accepted
- `cart/decorators.py:7-13` — only `quantity > stock` is rejected; `quantity <= 0` is allowed (negative totals), and the check is racy.
- Fix: require `1 <= quantity <= stock`.

### 17. N+1 queries
- `orders/views.py:22-27` (loop), `orders/views.py:53-56` — `order.products.all()` followed by per-row lookups.
- Fix: use `prefetch_related('products__product')`.

### 18. Login `redirect_field_name` misuse
- `users/urls.py:11` — `redirect_field_name='product_list'` should be a query-string param name (e.g. `'next'`), not a URL name; combined with `LOGIN_REDIRECT_URL` it works by accident.
- Fix: drop the argument (default `'next'`) or set it correctly.

### 19. `product_delete` decorator order breaks auth flow
- `products/views.py:63-66` — `member_is_owner_of_product` wraps `login_required`, so anonymous users get a 403 instead of a login redirect, and a GET (or missing `product_id`) raises `KeyError` before `require_http_methods` can reject it.
- Fix: move `@require_http_methods(['POST'])` and `@login_required` above the ownership check; use `request.POST.get(...)`.

### 20. Duplicate product results in search
- See P1 #6 — same product returned once per matched token.

### 21. Hardcoded sender address
- `orders/tasks.py:46` — `from_email='shopEveryThing@myshop.com'` must be a verified SendGrid sender or mail is rejected/deferred. Make it a setting.

### 22. Dev database and media committed to git
- `db.sqlite3` (contains real user accounts / password hashes) and `media/` (product images) are tracked. Add both to `.gitignore` and rotate any credentials; keep media out of the repo.

## P3 — Low (hygiene / maintenance)

### 23. Celery settings typos
- `shop/settings.py:162,166` — `CELERY_ACCPET_CONTENT` (typo for `CELERY_ACCEPT_CONTENT`) and `CELERY_TIMEZONE` set to a list instead of a string. Fix both (and confirm the cache/worker still behave).

### 24. Debug `print` statements left in views
- `cart/views.py:17-18,27`, `cart/decorators.py:11`, `orders/views.py:55`, `orders/tasks.py:15`, `products/models.py:44`. Remove or replace with logging.

### 25. No tests outside `products/tests/`
- `orders/tests.py`, `cart/tests.py`, `api/tests.py`, `users/tests.py` are empty stubs. Add regression tests for the fixes above (checkout atomicity, order authorization, search, signup).

### 26. Localization labels without any locale setup
- `products/forms.py`, `users/forms.py` use `_()` with Chinese strings, but `LANGUAGE_CODE='en-us'` and no `LOCALE_PATHS`/`make_messages` config exist. Either configure i18n properly or drop the `_()` wrappers.

### 27. Duplicated pagination logic
- `products/views.py:16-45` and `products/views.py:91-118` are near-identical. Extract a shared helper.
