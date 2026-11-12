# Storefront API v1

Use Zubda from your storefront's **server**, with a separate integration key for each application and environment. Never ship keys in browser JavaScript, mobile apps, URLs or logs. This API requires Pro or above (or an active trial). It does not grant access to payroll, accounting reports, arbitrary customer lists, payment collection or subscription billing.

Owners and admins manage keys in **Settings → Storefront API**. Keys have `catalogRead` and/or `ordersWrite` scopes, expire after 1–365 days, and are stored only as SHA-256 hashes of randomly generated 256-bit secrets. The full key is returned only on creation or replacement. Do not use your Paystack secret here.

Every storefront request sends `X-API-Key: <key>`. Cookie, Authorization and Origin headers are refused on this route. Send requests through a backend proxy that strips browser credentials. Responses use `Cache-Control: no-store`.

## Tenant and shopper boundaries

A key belongs to one Zubda business. Its tenant is derived from the authenticated key, not a client-supplied tenant header or request field. Management queries are restricted to the signed-in owner’s/admin’s business. Key hashes and full secrets are excluded from metadata responses.

The API key authenticates the store’s backend, not an individual shopper. Customer login belongs to the tenant’s storefront. The same person or email can be a customer of several businesses; each store keeps independent customer records, order access and commercial terms. Never merge or expose records across tenants solely because an email matches. Reusing customerId requires shopper ownership checks in your own server.

Revocation or expiry rejects subsequent requests; expiry is checked on each request without a cleanup job. Revocation does not cancel work that was already authorized and is in flight. Revoking an old credential does not revoke its valid replacement; revoke each active credential that should stop working.

## Catalog

- `GET /api/storefront/v1/locations` — active location IDs and names.
- `GET /api/storefront/v1/products?locationId=<uuid>&page=0&size=25` — page size 1–100; stable name/ID ordering. Active, sellable products only.

Catalog items contain product ID, SKU, name, description, image URL, unit price, sale currency, VAT rate, the product’s `taxInclusive` mode, inventory tracking and available quantity. Cost prices, supplier details, margins and accounting information are excluded. An untracked sales-only item has `availableQuantity: null`, not zero. Availability is a snapshot, not a reservation. Serialized/batched items are allocated by the team at fulfillment.

## Submit an order

`POST /api/storefront/v1/orders`, with `Content-Type: application/json` and a stable `Idempotency-Key` of 1–100 letters, digits, `.`, `_`, `:` or `-`:

```json
{
  "locationId": "YOUR_LOCATION_UUID",
  "customer": {
    "name": "Customer name",
    "email": "customer@example.com",
    "phone": "+254700000000",
    "address": "Delivery address"
  },
  "lines": [{ "productId": "YOUR_PRODUCT_UUID", "quantity": 2 }],
  "notes": "Delivery instructions"
}
```

Provide either customer details or a recorded `customerId`, never both. New buyer details create a customer; reuse the returned `customerId` for repeat buyers your store recognizes. Do not let one shopper choose another shopper's customer ID. The store's backend owns shopper authorization.

There are 1–100 lines, positive quantities up to three decimals. A new product inherits the company’s inclusive/exclusive pricing mode unless explicitly set. Catalog consumers must honor `taxInclusive`: exclusive prices have VAT added; inclusive prices already contain it. Historical order lines keep their recorded mode.

Prices and VAT come from the server catalog; shoppers cannot supply discounts, prices, payment status, serials or fulfillment status. All lines must use one currency. Foreign-currency orders require configured exchange rates; the order records the current rate. Amounts must fit the ledger's precision.

The response includes `id`, `orderNumber`, `DRAFT`, `UNPAID`, total, amount paid, currency and customer ID. Submission does not collect money, reserve/deduct stock, allocate serials or recognize revenue. Review and fulfill in Zubda; record and verify actual payments through the normal sales workflow. Do not mark a storefront payment successful from a redirect alone.

The order, customer, retry record and device sync facts commit together. Repeating the same key and request returns the same order ID. Reusing a key with different details returns **409**. Keep the key stable after timeouts; do not generate a new key for a network retry. Idempotency records are retained for 90 days by default; after that window an old key may be accepted again, so retain retry state for at least as long as your own retry policy.

`GET /api/storefront/v1/orders/<id>` returns the current summary only for this integration application's orders. Polling remains available as a reconciliation path.

## Webhooks

Configure a webhook on the integration key:

```http
PUT /api/integrations/keys/<id>/webhook
Content-Type: application/json

{ "url": "https://store.example.com/zubda/orders" }
```

The response contains the signing secret **once**. Store it server-side. Only HTTPS URLs are accepted, and loopback/private/link-local targets are refused. Removing the webhook with `DELETE /api/integrations/keys/<id>/webhook` stops future deliveries without revoking the key.

Order status changes are POSTed as JSON with:

- `X-Zubda-Event: order.status_changed`
- `X-Zubda-Delivery: <delivery uuid>` (use it to deduplicate)
- `X-Zubda-Timestamp: <unix seconds>`
- `X-Zubda-Signature: sha256=<hmac>`

The signature is HMAC-SHA256 over `<timestamp>.<raw body>` using the signing secret. Verify the timestamp is fresh and compare the signature in constant time before acting. Deliveries are durable and retried with backoff up to six attempts; a receiver may see duplicates after a timeout, so processing must be idempotent. Payload contains `event`, `orderId`, `orderNumber`, `status`, `paymentStatus`, `total`, `amountPaid`, `currency`, `customerId` and `occurredAt`.

## Replace or revoke credentials

Use **Replace key**, configure the replacement on your server, verify a catalog request, then revoke the old key. Replacement retains the same application identity, order visibility and idempotency namespace. The old key remains usable until revoked or expired, allowing an orderly rollout. Creating a separate integration is a new namespace.

Management endpoints use an owner's/admin's normal authenticated session (and CSRF token for cookie writes):

- `GET /api/integrations/keys` — metadata, never token hashes or secrets.
- `POST /api/integrations/keys` — `{ "name": "Online store", "catalogRead": true, "ordersWrite": false, "expiresInDays": 90 }`.
- `POST /api/integrations/keys/<id>/rotate` — replacement credential, 90-day expiry, same scopes.
- `DELETE /api/integrations/keys/<id>` — idempotent revocation. Listing and revocation remain available after a plan downgrade.

## Errors and operation

The organization has the same subscription grace as normal sessions: seven days of full access after expiry, then read-only through day 14. Keys themselves stop at their own expiry immediately.

401 means missing, expired or revoked credentials (or an inactive/locked organization); 403 means missing scope; 402 means the plan no longer includes API access; 400 means invalid input; 404 means the integration cannot see that order; 409 means conflicting retry details. Limit requests and retry transient failures with backoff. The backend applies 120 requests per minute per IP and key. Counters live in the configured cache: shared across instances with Redis, per instance in memory mode. It returns 429 with `Retry-After: 60`.

Do not interpret a timeout as an order failure: retry the original body and idempotency key. Recheck catalog prices and order totals on your storefront. The shopper-facing service must enforce its own authentication, checkout limits and customer ownership.

MCP and agent tooling are a later phase. Keep future machine actions behind explicit scopes, audited business commands and the same retry protections; no agent endpoints are introduced by this release.
