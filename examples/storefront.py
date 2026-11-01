#!/usr/bin/env python3
"""Server-side Storefront API v1 example. Python 3.10+, no dependencies.

export ZUBDA_API_KEY='your scoped key'  # set this in your server secret manager
python3 examples/storefront.py locations
python3 examples/storefront.py products --location YOUR_LOCATION_UUID
python3 examples/storefront.py order --file /private/order.json --retry-key YOUR_CHECKOUT_ID

The order command creates a real unpaid draft. Run it only with permission in
your own test business. Reuse the same file and retry key after a timeout.
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = "https://api.zubda.co/api/storefront/v1"


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward credentials to a redirect target.
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("locations")
    products = commands.add_parser("products")
    products.add_argument("--location", required=True, type=uuid.UUID)
    products.add_argument("--page", type=int, default=0)
    products.add_argument("--size", type=int, default=25)
    order = commands.add_parser("order")
    order.add_argument("--file", required=True, type=Path)
    order.add_argument("--retry-key", required=True)
    status = commands.add_parser("status")
    status.add_argument("--id", required=True, type=uuid.UUID)
    args = parser.parse_args()
    key = os.environ.get("ZUBDA_API_KEY", "").strip()
    if not key or "\n" in key or "\r" in key:
        parser.error("Set ZUBDA_API_KEY on your server. Do not pass it as a command argument.")
    headers = {"X-API-Key": key, "Accept": "application/json"}
    data = None
    path = "/locations"
    if args.command == "products":
        if args.page < 0 or not 1 <= args.size <= 100:
            parser.error("page must be non-negative and size must be between 1 and 100")
        path = "/products?" + urllib.parse.urlencode({"locationId": str(args.location), "page": args.page, "size": args.size})
    elif args.command == "order":
        if not re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", args.retry_key):
            parser.error("retry-key must contain 1–100 letters, digits, dots, underscores, colons or hyphens")
        try:
            payload = json.loads(args.file.read_text())
            if not isinstance(payload, dict):
                raise ValueError()
            data = json.dumps(payload).encode()
        except (OSError, ValueError):
            parser.error("file must be a readable JSON object")
        path = "/orders"
        headers.update({"Content-Type": "application/json", "Idempotency-Key": args.retry_key})
    elif args.command == "status":
        path = "/orders/" + str(args.id)
    request = urllib.request.Request(BASE + path, data=data, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirects).open(request, timeout=15) as response:
            result = json.load(response)
        # Contains business data: write only to a private terminal, not public logs.
        print(json.dumps(result, indent=2))
    except urllib.error.HTTPError as error:
        # Do not dump headers, provider errors or customer-bearing response bodies.
        print(f"Zubda returned HTTP {error.code}. See docs/storefront-api-v1.md for recovery.", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError):
        print("No usable response. For orders, retry with the original file and retry key; do not create a new checkout.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
