# Zubda developer community

Build connections to Zubda, ask integration questions, share examples and suggest improvements.

- [Questions and answers](https://github.com/matrixjnr/zubda-community/discussions/categories/q-a)
- [Feature requests](https://github.com/matrixjnr/zubda-community/discussions/categories/ideas)
- [Share your integration](https://github.com/matrixjnr/zubda-community/discussions/categories/show-and-tell)
- [Announcements](https://github.com/matrixjnr/zubda-community/discussions/categories/announcements)
- [Storefront API v1 guide](docs/storefront-api-v1.md)
- [Server-side Python example](examples/storefront.py)
- [Zubda portal](https://portal.zubda.co)

## What is available today?

The public **Storefront API v1** supports reading active locations, catalog and availability, submitting unpaid draft orders, and checking orders created by the same integration. It requires Pro or above, or an active trial. It does not expose the ERP's internal endpoints or provide payment collection, payroll, accounting reports or outbound order webhooks.

Create a scoped, expiring key in **Portal → Settings → Storefront API**. Keep it in a server environment variable; never include it in browser code, mobile apps, screenshots or a public discussion. Prices and taxes are calculated by Zubda, and submission does not reserve stock or recognize revenue.

This repository contains public documentation and examples. Zubda ERP source code and customer data are not hosted here. Hosted-store plans are a separate product capability; they do not change the Pro requirement for third-party API keys.

## Ask a useful question

Search existing discussions first. Include the endpoint, HTTP status, Zubda app version if relevant, expected result and a minimal example with synthetic data. Redact keys, authorization headers, cookies, customer details, private order identifiers and payment information. A reproducible example helps other developers answer.

Use **Q&A** for implementation help, **Ideas** for proposals, and **Show and tell** for reusable integrations. Discussion is community support; it is not a guaranteed response-time or product-roadmap commitment. For account-specific help, use [Zubda contact](https://www.zubda.co/contact/).

## Security and participation

Report vulnerabilities privately to **security@zubda.co**; do not publish exploit details or real credentials. See [SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Documentation and examples in this repository use the MIT license. This does not license the Zubda application, trademarks or third-party integrations.
