# kortingzoeker.com — product and launch next steps

Last updated: 10 October 2026

This document captures the product review, ChatGPT App Directory preparation,
and the proposed future coupon-code/affiliate feature so work can resume later.

## Product direction

The initial product is a Dutch shopping assistant in ChatGPT. The current v1
uses Picnic promotions to help users discover deals, create grocery lists, and
suggest meals within a budget.

The strongest current promise is:

> Turn current supermarket deals into useful meals and grocery lists.

The longer-term brand opportunity is broader:

> Find relevant discounts while planning, shopping, or checking out.

The broader direction should not dilute the grocery launch before its
activation and repeat-use hypotheses have been tested.

## Current implementation

The MCP server currently exposes:

- `list_supermarkets`
- `get_current_discounts(supermarket_id, category?)`

Picnic is the only supported supermarket. The server includes structured deal
data, read-only annotations, tool-routing instructions, analytics middleware,
and parser/server tests.

The App Directory preparation branch also includes:

- Product rename from `koopje.ai` to `kortingzoeker.com`
- Dutch and English `/privacy`, `/terms`, and `/support` pages
- Footer links to all policy/support pages
- App Directory metadata under `submission/`
- Exactly five positive and three negative review cases
- `scripts/generate_plugin_package.py`
- `make plugin-package`, which generates:
  - `dist/plugin/plugin.json`
  - `dist/plugin/mcp.json`
  - listing icons
  - onboarding skill
  - review-case document
  - `dist/kortingzoeker-chatgpt-plugin.zip`

## Remaining grocery launch work

### Product and data reliability

- [ ] Add `retrieved_at`, source, and validity/expiry metadata to deal results.
- [ ] Automate deal refreshes.
- [ ] Monitor freshness, deal counts, parser failures, and empty feeds.
- [ ] Return a clear unavailable/stale result instead of describing old data as
      current.
- [ ] Validate every claim such as "live" or "save up to 30%"; remove claims
      that cannot be substantiated.
- [ ] Resolve authorization and terms-of-service questions around the Picnic
      data source before public review.
- [ ] Review response size when all categories are returned.
- [ ] Consider search/filter inputs when the catalog grows.

### Privacy and legal

- [ ] Ensure the published privacy policy matches actual PostHog and log
      retention settings.
- [ ] Stop sending raw dietary, allergy, household, medical, or other sensitive
      prompt values to analytics.
- [ ] Confirm the legal operator/company identity and contact information that
      must appear on the site.
- [ ] Have the privacy policy and terms reviewed for the intended Netherlands/EU
      launch. The repository copy is a product draft, not legal advice.
- [ ] Verify `support@kortingzoeker.com` is active and monitored.

### Production and App Directory

- [ ] Deploy the website to `https://kortingzoeker.com`.
- [ ] Deploy a stable universal MCP endpoint, currently planned as
      `https://mcp.kortingzoeker.com/mcp`.
- [ ] Add production health and freshness monitoring.
- [ ] Record a reviewer-accessible demo and replace the placeholder
      `https://kortingzoeker.com/review/demo`.
- [ ] Generate the final package with `make plugin-package`.
- [ ] Verify the OpenAI publisher organization.
- [ ] Upload the generated ZIP.
- [ ] Connect the production MCP endpoint with no authentication for v1.
- [ ] Complete domain verification.
- [ ] Scan tools and resolve automated findings.
- [ ] Run all five positive and three negative review cases against production.
- [ ] Confirm Netherlands availability and Dutch/English listing content.
- [ ] Submit for review.
- [ ] After approval, publish and replace the generic landing CTA with the real
      App Directory URL.

OpenAI references:

- [App submission](https://developers.openai.com/apps-sdk/deploy/submission)
- [App submission guidelines](https://developers.openai.com/apps-sdk/app-submission-guidelines)
- [Plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines)

## Launch validation

Installation alone measures curiosity, not value. Track this funnel:

1. Listing viewed
2. App installed
3. First successful deal-backed result
4. Grocery list used or copied
5. Second session within 14 days
6. Continued weekly use

Recommended primary metric:

> Weekly users who successfully generate a deal-backed list or meal plan.

Useful supporting metrics:

- Activation rate after installation
- Tool success and no-result rates
- Data freshness at each successful request
- Repeat use after 7 and 14 days
- Incorrect-price reports
- List-copy or equivalent engagement

## Future coupon-code tool

### User problem

A user is shopping for a physical product, ChatGPT finds or discusses a product
URL, and kortingzoeker.com checks whether an applicable coupon code exists.

Example:

```text
User selects shoes
    -> ChatGPT calls find_discount_codes(product_url)
    -> kortingzoeker.com returns verified candidates
    -> user copies a code or opens the retailer
```

The tool must never claim that it applied a code, placed an order, or
guaranteed acceptance.

### Proposed data tool

```text
find_discount_codes(
  product_url,
  country?,
  cart_total?,
  customer_type?
)
```

Only `product_url` should be required.

Suggested description:

> Use this when the user provides or selects a product/store URL and wants a
> coupon, promo, voucher, or discount code. Returns known codes and their
> restrictions. It does not apply codes, modify carts, purchase products, or
> guarantee acceptance. Do not use it for supermarket deal discovery without a
> product URL.

Suggested annotations for a controlled coupon catalog:

```json
{
  "readOnlyHint": true,
  "destructiveHint": false,
  "idempotentHint": true,
  "openWorldHint": false
}
```

Use `openWorldHint: true` if implementation searches or fetches arbitrary
websites rather than querying a bounded catalog.

Suggested result shape:

```json
{
  "merchant": {
    "name": "Example Shoes",
    "domain": "example.com"
  },
  "product": {
    "url": "https://example.com/products/running-shoe"
  },
  "checked_at": "2026-10-10T09:00:00Z",
  "offers": [
    {
      "id": "offer_01",
      "code": "WELCOME10",
      "description": "10% off for new customers",
      "discount": {
        "type": "percentage",
        "value": 10
      },
      "verification_status": "verified",
      "last_verified_at": "2026-10-08T12:00:00Z",
      "expires_at": null,
      "restrictions": [
        "New customers only",
        "Excludes sale products"
      ],
      "minimum_spend": null
    }
  ],
  "message": "Codes can expire or have additional checkout restrictions."
}
```

Verification statuses:

- `verified`: confirmed through an authorized merchant or feed
- `recently_reported`: recently reported working but not directly confirmed
- `unverified`: known candidate with uncertain validity

Never describe a reported or unverified code as valid. Return a small number of
ranked results, ideally no more than five.

### Proposed render tool and UI

Use a separate rendering tool:

```text
render_discount_codes(offer_ids)
```

The data tool remains reusable by the model. The render tool owns an Apps SDK
resource and displays cards such as:

```text
Example Shoes

WELCOME10
10% for new customers

Verified 2 days ago
Excludes sale products

[Copy code]  [Open retailer]

Affiliate link — we may earn a commission at no extra cost to you.
Final eligibility and price are confirmed by the retailer.
```

Use "Open retailer," not "Claim discount," because acceptance is not
guaranteed. Keep affiliate URLs out of model-visible content where possible;
pass short-lived URLs to the widget through tool-response metadata.

The widget can open the destination with:

```ts
await window.openai.openExternal({
  href: affiliateUrl,
  redirectUrl: false,
});
```

Declare the required affiliate-network or merchant origins in the widget CSP:

```json
{
  "openai/widgetCSP": {
    "redirect_domains": [
      "https://affiliate-network.example",
      "https://merchant.example"
    ]
  }
}
```

Do not use redirects to evade ChatGPT's safe-link UX. If destinations cannot be
declared safely, accept the safe-link confirmation.

### Link destination

Preferred flow:

```text
ChatGPT widget
    -> authorized affiliate tracking link
    -> retailer product/offer page
```

Do not force the user through a kortingzoeker.com landing page solely for
tracking or ad impressions. An intermediate offer page is justified only when
it adds material value, such as complete restrictions, alternatives, or
verification details.

Never:

- Automatically open the link
- Hide the destination merchant
- Send the user directly into an embedded third-party checkout
- Rank offers primarily by commission
- Guarantee that a code will work

### Coupon sourcing

Preferred source order:

1. Merchant or affiliate-network feeds
2. Direct merchant partnerships
3. Merchant-submitted campaigns
4. Human-curated codes
5. Licensed coupon aggregators
6. User reports as a secondary signal

Do not scrape coupon sites or retailer pages without authorization. OpenAI's
guidelines prohibit unauthorized third-party scraping and unofficial
connectors.

### URL safety

For the first version, do not crawl arbitrary supplied pages:

1. Accept only HTTP/HTTPS URLs.
2. Reject embedded credentials.
3. Remove fragments and tracking/query parameters when they are not required.
4. Resolve the registrable domain.
5. Match the domain against the controlled merchant catalog.
6. Query the coupon database.

If page parsing is introduced later, use merchant APIs or explicitly authorized
feeds. Never pass raw third-party page content to the model because it may
contain prompt injection.

### Ranking

Rank using:

1. Verification status
2. Expected user savings
3. Product applicability
4. Verification recency
5. Restrictions
6. Historical success rate
7. Expiration

Do not rank by affiliate commission. Clearly label sponsored placement and keep
it separate from organic ranking.

### Affiliate monetization and OpenAI policy

Affiliate monetization is not explicitly prohibited in the current public
guidelines, but it is also not explicitly guaranteed to be accepted.

Relevant constraints:

- Current app commerce support is limited to physical goods.
- Apps must not serve advertisements or exist primarily as advertising
  vehicles.
- The app must provide standalone utility.
- Third-party feeds and APIs must be authorized.
- Third-party checkout must not be embedded.
- Affiliate relationships and tracking must be disclosed clearly.
- Directory copy should describe functionality without advertising specific
  prices or promotional offers.

The coupon experience therefore has material review risk. Seek early OpenAI
review clarification before making affiliate revenue a core dependency.

If this feature is added:

- [ ] Change the submission manifest from `commerce: false` to `commerce: true`.
- [ ] Explain that the app finds coupons for physical goods and links to
      retailers.
- [ ] State that kortingzoeker.com does not process payment or fulfill orders.
- [ ] Update privacy and terms for product URLs, affiliate networks, click
      attribution, retention, and commissions.
- [ ] Put a disclosure next to each outbound action:
      "Affiliate link — kortingzoeker.com may receive a commission at no extra
      cost to you."
- [ ] Replace some existing review cases rather than appending cases because
      initial MCP review requires exactly five positive and three negative
      cases.

### Affiliate attribution

Suggested flow:

```text
Coupon catalog
    -> stable offer ID
    -> short-lived authorized affiliate URL
    -> user-initiated click
    -> affiliate network conversion reporting
    -> payout reconciliation
```

Track only what is needed:

- Random click/reference ID
- Offer ID
- Merchant/campaign ID
- Timestamp
- Conversion amount and commission

Do not send `openai/subject`, prompt contents, household information, or
dietary information to an affiliate network.

### Future feedback tool

After the lookup experience works, consider:

```text
report_discount_code_result(coupon_id, result, savings?)
```

Use opaque IDs, abuse controls, and explicit write annotations:

```json
{
  "readOnlyHint": false,
  "destructiveHint": false,
  "openWorldHint": false
}
```

Do not let a small number of anonymous reports automatically determine
verification status.

### Coupon product metrics

Primary metric:

> Percentage of coupon searches that produce a code confirmed to work.

Supporting metrics:

- Supported-merchant rate
- Searches with at least one result
- Verified-code coverage
- Verification age
- Worked/did-not-work feedback
- Estimated user savings
- Affiliate click-through rate
- Attributed conversion rate
- Repeat usage

## Recommended sequencing

1. Complete and validate the Picnic grocery launch.
2. Confirm OpenAI's treatment of disclosed affiliate coupon links.
3. Secure one authorized affiliate/feed partner.
4. Build a controlled catalog for 10–20 Dutch physical-goods retailers.
5. Add `find_discount_codes` without arbitrary web crawling.
6. Test coupon accuracy before adding outbound links.
7. Add the coupon widget with disclosure and user-initiated retailer links.
8. Update policies, submission metadata, commerce declaration, and review cases.
9. Measure confirmed success rate before expanding merchant coverage.

The defensible coupon proposition is not the number of codes returned. It is
that the first code shown is likely to work.
