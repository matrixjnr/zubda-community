# Storefront API v1

Use Zubda from your storefront's **server**, with a separate integration key for each application and environment. Never ship keys in browser JavaScript, mobile apps, URLs or logs. This API requires Pro or above (or an active trial). It does not grant access to payroll, accounting reports, arbitrary customer lists, payment collection or subscription billing.

Owners and admins manage keys in **Settings → Storefront API**. Keys have `catalogRead` and/or `ordersWrite` scopes, expire after 1–365 days, and are stored only as SHA-256 hashes of randomly generated 256-bit secrets. The full key is returned only on creation or replacement. Do not use your Paystack secret here.

Every storefront request sends `X-API-Key: <key>`. Cookie, Authorization and Origin headers are refused on this route. Send requests through a backend proxy that strips browser credentials. Responses use `Cache-Control: no-store`.

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

The order, customer, retry record and device sync facts commit together. Repeating the same key and request returns the same order ID. Reusing a key with different details returns **409**. Keep the key stable after timeouts; do not generate a new key for a network retry.

`GET /api/storefront/v1/orders/<id>` returns the current summary only for this integration application's orders. Poll it for status; v1 does not provide outbound storefront webhooks.

## Replace or revoke credentials

Use **Replace key**, configure the replacement on your server, verify a catalog request, then revoke the old key. Replacement retains the same application identity, order visibility and idempotency namespace. The old key remains usable until revoked or expired, allowing an orderly rollout. Creating a separate integration is a new namespace.

Management endpoints use an owner's/admin's normal authenticated session (and CSRF token for cookie writes):

- `GET /api/integrations/keys` — metadata, never token hashes or secrets.
- `POST /api/integrations/keys` — `{ "name": "Online store", "catalogRead": true, "ordersWrite": false, "expiresInDays": 90 }`.
- `POST /api/integrations/keys/<id>/rotate` — replacement credential, 90-day expiry, same scopes.
- `DELETE /api/integrations/keys/<id>` — idempotent revocation. Listing and revocation remain available after a plan downgrade.

## Errors and operation

The organization has the same subscription grace as normal sessions: seven days of full access after expiry, then read-only through day 14. Keys themselves stop at their own expiry immediately.

401 means missing, expired or revoked credentials (or an inactive/locked organization); 403 means missing scope; 402 means the plan no longer includes API access; 400 means invalid input; 404 means the integration cannot see that order; 409 means conflicting retry details. Limit requests and retry transient failures with backoff. The backend applies 120 requests per minute per IP and key per instance, returns 429 with `Retry-After: 60`; configure shared rate limits at the reverse proxy for multiple instances.

Do not interpret a timeout as an order failure: retry the original body and idempotency key. Recheck catalog prices and order totals on your storefront. The shopper-facing service must enforce its own authentication, checkout limits and customer ownership.

MCP and agent tooling are a later phase. Keep future machine actions behind explicit scopes, audited business commands and the same retry protections; no agent endpoints are introduced by this release.
